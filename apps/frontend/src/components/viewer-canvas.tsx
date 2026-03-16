"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";
import { EffectComposer } from "three/examples/jsm/postprocessing/EffectComposer.js";
import { RenderPass } from "three/examples/jsm/postprocessing/RenderPass.js";
import { UnrealBloomPass } from "three/examples/jsm/postprocessing/UnrealBloomPass.js";

type ViewerCanvasProps = {
  modelUrl: string | null;
  ringParameters: {
    metal: "gold" | "rose_gold" | "platinum" | "silver";
    gemstone_type: "diamond" | "ruby" | "emerald" | "sapphire";
  } | null;
  ringSummary: {
    estimatedPriceUsd: number;
    manufacturabilityWarnings: { code: string; message: string }[];
  } | null;
};

type MaterialDiagnostics = {
  totalMeshes: number;
  settingMeshes: number;
  gemLikeMeshes: number;
  materialsAssigned: number;
  gemSelectionReason: string;
};

type ModelDiagnostics = {
  totalMeshes: number;
  missingNormalCount: number;
  invalidNormalCount: number;
  missingUvCount: number;
  mirroredScaleCount: number;
  boundsSize: { x: number; y: number; z: number };
  boundsCenter: { x: number; y: number; z: number };
};

type GeometryRepairDiagnostics = {
  repairedMeshes: number;
  repairedBecauseMissingNormals: number;
  repairedBecauseInvalidNormals: number;
};

export function ViewerCanvas({ modelUrl, ringParameters, ringSummary }: ViewerCanvasProps) {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const activeRootRef = useRef<THREE.Object3D | null>(null);
  const sceneRef = useRef<THREE.Scene | null>(null);
  const cameraRef = useRef<THREE.PerspectiveCamera | null>(null);
  const rendererRef = useRef<THREE.WebGLRenderer | null>(null);
  const composerRef = useRef<EffectComposer | null>(null);
  const bloomPassRef = useRef<UnrealBloomPass | null>(null);
  const controlsRef = useRef<OrbitControls | null>(null);
  const modelRootRef = useRef<THREE.Group | null>(null);
  const pmremGeneratorRef = useRef<THREE.PMREMGenerator | null>(null);
  const environmentRef = useRef<THREE.Texture | null>(null);
  const animationFrameRef = useRef<number>(0);
  const resizeHandlerRef = useRef<(() => void) | null>(null);
  const loaderRef = useRef<GLTFLoader | null>(null);
  const activeLoadTokenRef = useRef(0);
  const hasAutoFramedRef = useRef(false);
  const loadedRingIdRef = useRef<string | null>(null);
  const ringParametersRef = useRef<ViewerCanvasProps["ringParameters"]>(ringParameters);
  const isInteractingRef = useRef(false);
  const idleRotationYRef = useRef(0);
  const currentRotationSpeedRef = useRef(0);
  const lastFrameAtRef = useRef(0);
  const diagnosticsEnabledRef = useRef(process.env.NODE_ENV !== "production");
  const diagnosticTagRef = useRef(`viewer-${Math.random().toString(36).slice(2, 8)}`);

  const logDiag = (event: string, payload?: unknown, level: "info" | "warn" | "error" = "info") => {
    if (!diagnosticsEnabledRef.current) {
      return;
    }
    const tag = `[viewer-diag:${diagnosticTagRef.current}] ${event}`;
    if (level === "warn") {
      console.warn(tag, payload);
      return;
    }
    if (level === "error") {
      console.error(tag, payload);
      return;
    }
    console.info(tag, payload);
  };

  const disposeObjectResources = (object: THREE.Object3D | null) => {
    if (!object) {
      return;
    }
    object.traverse((node) => {
      if (!(node instanceof THREE.Mesh)) {
        return;
      }
      if (Array.isArray(node.material)) {
        node.material.forEach((material) => material.dispose());
      } else {
        node.material.dispose();
      }
      node.geometry.dispose();
    });
  };

  const parseRingIdFromModelUrl = (url: string | null): string | null => {
    if (!url) {
      return null;
    }
    const match = url.match(/\/artifacts\/([^/]+)\/model\.glb/i);
    return match?.[1] ?? null;
  };

  const fitCameraToObject = (object: THREE.Object3D) => {
    const camera = cameraRef.current;
    const controls = controlsRef.current;
    if (!camera || !controls) {
      return;
    }

    const box = new THREE.Box3().setFromObject(object);
    if (box.isEmpty()) {
      return;
    }

    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    const maxDimension = Math.max(size.x, size.y, size.z);
    const distance = Math.max(maxDimension * 1.6, 4);

    camera.position.set(center.x + distance * 0.9, center.y + distance * 0.7, center.z + distance * 0.9);
    controls.target.copy(center);
    controls.update();
  };

  const applyMaterials = (
    root: THREE.Object3D,
    params: ViewerCanvasProps["ringParameters"]
  ): MaterialDiagnostics => {
    const metalPalette: Record<string, string> = {
      gold: "#d4af37",
      rose_gold: "#b76e79",
      platinum: "#d9dee7",
      silver: "#bcc5ce",
    };
    const gemPalette: Record<string, string> = {
      diamond: "#e8f3ff",
      ruby: "#c81d3a",
      emerald: "#0f9d58",
      sapphire: "#2d5bff",
    };

    const metalColor = new THREE.Color(metalPalette[params?.metal ?? "gold"]);
    const gemColor = new THREE.Color(gemPalette[params?.gemstone_type ?? "diamond"]);
    const selectedMetal = params?.metal ?? "gold";
    const selectedGem = params?.gemstone_type ?? "diamond";

    const metalPreset = {
      gold: { roughness: 0.15, clearcoat: 1.0, clearcoatRoughness: 0.035, envMapIntensity: 4.5 },
      rose_gold: { roughness: 0.17, clearcoat: 1.0, clearcoatRoughness: 0.04, envMapIntensity: 4.25 },
      platinum: { roughness: 0.11, clearcoat: 0.85, clearcoatRoughness: 0.028, envMapIntensity: 4.65 },
      silver: { roughness: 0.1, clearcoat: 0.82, clearcoatRoughness: 0.026, envMapIntensity: 4.75 },
    }[selectedMetal];

    const gemPreset = {
      diamond: {
        ior: 2.42,
        roughness: 0.008,
        transmission: 1.0,
        thickness: 1.9,
        envMapIntensity: 5.4,
        attenuationDistance: 4.5,
        attenuationColor: "#f8fcff",
        dispersion: 0.048,
      },
      ruby: {
        ior: 1.77,
        roughness: 0.018,
        transmission: 0.97,
        thickness: 1.45,
        envMapIntensity: 4.45,
        attenuationDistance: 1.45,
        attenuationColor: "#8f001a",
        dispersion: 0.02,
      },
      emerald: {
        ior: 1.58,
        roughness: 0.023,
        transmission: 0.96,
        thickness: 1.52,
        envMapIntensity: 4.25,
        attenuationDistance: 1.2,
        attenuationColor: "#045a2a",
        dispersion: 0.017,
      },
      sapphire: {
        ior: 1.77,
        roughness: 0.017,
        transmission: 0.97,
        thickness: 1.5,
        envMapIntensity: 4.65,
        attenuationDistance: 1.55,
        attenuationColor: "#0f2fbd",
        dispersion: 0.023,
      },
    }[selectedGem];

    const buildHint = (node: THREE.Mesh, source?: THREE.Material): string => {
      const pathHints: string[] = [];
      let cursor: THREE.Object3D | null = node;
      while (cursor) {
        pathHints.push(cursor.name ?? "");
        cursor = cursor.parent;
      }
      return `${node.name ?? ""} ${source?.name ?? ""} ${pathHints.join(" ")}`.toLowerCase();
    };

    const classifyGemLike = (node: THREE.Mesh, source?: THREE.Material): boolean => {
      const hint = buildHint(node, source);
      if (
        hint.includes("gem") ||
        hint.includes("stone") ||
        hint.includes("diamond") ||
        hint.includes("ruby") ||
        hint.includes("emerald") ||
        hint.includes("sapphire")
      ) {
        return true;
      }

      return false;
    };

    const buildGemMaterial = (source?: THREE.Material) => {
      const base = source?.clone() as THREE.MeshPhysicalMaterial | undefined;
      const gemMaterial =
        base instanceof THREE.MeshPhysicalMaterial
          ? base
          : new THREE.MeshPhysicalMaterial();

      gemMaterial.name = source?.name ?? gemMaterial.name;
      gemMaterial.vertexColors = false;
      gemMaterial.color = selectedGem === "diamond" ? new THREE.Color("#f4f8ff") : gemColor.clone();
      gemMaterial.emissive = new THREE.Color("#000000");
      gemMaterial.metalness = 0.0;
      gemMaterial.roughness = gemPreset.roughness;
      gemMaterial.transmission = gemPreset.transmission;
      gemMaterial.thickness = gemPreset.thickness;
      gemMaterial.ior = gemPreset.ior;
      gemMaterial.clearcoat = 0.55;
      gemMaterial.clearcoatRoughness = 0.015;
      gemMaterial.reflectivity = 1.0;
      gemMaterial.specularIntensity = 1.0;
      gemMaterial.envMapIntensity = gemPreset.envMapIntensity;
      gemMaterial.attenuationDistance = gemPreset.attenuationDistance;
      gemMaterial.attenuationColor = new THREE.Color(gemPreset.attenuationColor);
      gemMaterial.transparent = true;
      if ("dispersion" in gemMaterial) {
        (gemMaterial as THREE.MeshPhysicalMaterial & { dispersion?: number }).dispersion = gemPreset.dispersion;
      }
      gemMaterial.needsUpdate = true;
      return gemMaterial;
    };

    const buildMetalMaterial = (source?: THREE.Material) => {
      const base = source?.clone() as THREE.MeshPhysicalMaterial | undefined;
      const metalMaterial =
        base instanceof THREE.MeshPhysicalMaterial
          ? base
          : new THREE.MeshPhysicalMaterial();

      metalMaterial.name = source?.name ?? metalMaterial.name;
      metalMaterial.vertexColors = false;
      metalMaterial.color = metalColor.clone();
      metalMaterial.emissive = new THREE.Color("#000000");
      metalMaterial.metalness = 1.0;
      metalMaterial.roughness = metalPreset.roughness;
      metalMaterial.clearcoat = metalPreset.clearcoat;
      metalMaterial.clearcoatRoughness = metalPreset.clearcoatRoughness;
      metalMaterial.reflectivity = 1.0;
      metalMaterial.specularIntensity = 1.0;
      metalMaterial.envMapIntensity = metalPreset.envMapIntensity;
      metalMaterial.transmission = 0.0;
      metalMaterial.needsUpdate = true;
      return metalMaterial;
    };

    const meshes: THREE.Mesh[] = [];
    root.traverse((node) => {
      if (node instanceof THREE.Mesh) {
        meshes.push(node);
      }
    });

    const settingMeshes = meshes.filter((mesh) => {
      const source = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
      const hint = buildHint(mesh, source ?? undefined);
      return (
        hint.includes("setting.") ||
        hint.includes("peghead") ||
        hint.includes("basket") ||
        hint.includes("bezel") ||
        hint.includes("halo") ||
        hint.includes("cluster")
      );
    });

    const gemLikeMeshes = new Set<THREE.Mesh>();
    for (const mesh of meshes) {
      const source = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
      if (classifyGemLike(mesh, source ?? undefined)) {
        gemLikeMeshes.add(mesh);
      }
    }

    if (settingMeshes.length > 0) {
      const settingWeight = settingMeshes.reduce((acc, mesh) => acc + mesh.geometry.attributes.position.count, 0);
      const gemWeight = Array.from(gemLikeMeshes).reduce(
        (acc, mesh) => acc + mesh.geometry.attributes.position.count,
        0
      );
      if (gemWeight < settingWeight * 0.35) {
        for (const mesh of settingMeshes) {
          gemLikeMeshes.add(mesh);
        }
      }
    }

    let gemSelectionReason = "hint-matches";

    if (gemLikeMeshes.size === 0 && meshes.length > 0) {
      if (settingMeshes.length > 0) {
        for (const mesh of settingMeshes) {
          gemLikeMeshes.add(mesh);
        }
        gemSelectionReason = "setting-fallback";
      } else {
        let picked: THREE.Mesh | null = null;
        let bestScore = -Infinity;
        for (const mesh of meshes) {
          const box = new THREE.Box3().setFromObject(mesh);
          const size = box.getSize(new THREE.Vector3());
          const center = box.getCenter(new THREE.Vector3());
          const score = center.z - size.length() * 0.1;
          if (score > bestScore) {
            bestScore = score;
            picked = mesh;
          }
        }
        if (picked) {
          gemLikeMeshes.add(picked);
          gemSelectionReason = "single-front-fallback";
        }
      }
    } else if (settingMeshes.length > 0) {
      const settingWeight = settingMeshes.reduce((acc, mesh) => acc + mesh.geometry.attributes.position.count, 0);
      const gemWeight = Array.from(gemLikeMeshes).reduce(
        (acc, mesh) => acc + mesh.geometry.attributes.position.count,
        0
      );
      if (gemWeight < settingWeight * 0.35) {
        gemSelectionReason = "setting-promotion";
      }
    }

    let materialsAssigned = 0;
    for (const mesh of meshes) {
      const isGemLike = gemLikeMeshes.has(mesh);
      if (Array.isArray(mesh.material)) {
        materialsAssigned += mesh.material.length;
        mesh.material = mesh.material.map((sourceMaterial) =>
          isGemLike ? buildGemMaterial(sourceMaterial) : buildMetalMaterial(sourceMaterial)
        );
      } else {
        materialsAssigned += 1;
        mesh.material = isGemLike
          ? buildGemMaterial(mesh.material ?? undefined)
          : buildMetalMaterial(mesh.material ?? undefined);
      }
      mesh.castShadow = true;
      mesh.receiveShadow = true;
    }

    return {
      totalMeshes: meshes.length,
      settingMeshes: settingMeshes.length,
      gemLikeMeshes: gemLikeMeshes.size,
      materialsAssigned,
      gemSelectionReason,
    };
  };

  const inspectModelGeometry = (root: THREE.Object3D): ModelDiagnostics => {
    const box = new THREE.Box3().setFromObject(root);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());

    let totalMeshes = 0;
    let missingNormalCount = 0;
    let invalidNormalCount = 0;
    let missingUvCount = 0;
    let mirroredScaleCount = 0;

    root.traverse((node) => {
      if (!(node instanceof THREE.Mesh)) {
        return;
      }
      totalMeshes += 1;
      if (!node.geometry.attributes.normal) {
        missingNormalCount += 1;
      } else {
        const normalAttr = node.geometry.attributes.normal;
        let isInvalid = false;
        for (let i = 0; i < normalAttr.count; i += 1) {
          const nx = normalAttr.getX(i);
          const ny = normalAttr.getY(i);
          const nz = normalAttr.getZ(i);
          const lengthSq = nx * nx + ny * ny + nz * nz;
          if (!Number.isFinite(lengthSq) || lengthSq < 1e-12) {
            isInvalid = true;
            break;
          }
        }
        if (isInvalid) {
          invalidNormalCount += 1;
        }
      }
      if (!node.geometry.attributes.uv) {
        missingUvCount += 1;
      }
      node.updateWorldMatrix(true, false);
      if (node.matrixWorld.determinant() < 0) {
        mirroredScaleCount += 1;
      }
    });

    return {
      totalMeshes,
      missingNormalCount,
      invalidNormalCount,
      missingUvCount,
      mirroredScaleCount,
      boundsSize: { x: size.x, y: size.y, z: size.z },
      boundsCenter: { x: center.x, y: center.y, z: center.z },
    };
  };

  const repairGeometryForShading = (root: THREE.Object3D): GeometryRepairDiagnostics => {
    let repairedMeshes = 0;
    let repairedBecauseMissingNormals = 0;
    let repairedBecauseInvalidNormals = 0;

    root.traverse((node) => {
      if (!(node instanceof THREE.Mesh)) {
        return;
      }

      const geometry = node.geometry;
      const normalAttr = geometry.attributes.normal;
      let shouldRepair = !normalAttr;
      let invalidNormals = false;

      if (normalAttr) {
        for (let i = 0; i < normalAttr.count; i += 1) {
          const nx = normalAttr.getX(i);
          const ny = normalAttr.getY(i);
          const nz = normalAttr.getZ(i);
          const lengthSq = nx * nx + ny * ny + nz * nz;
          if (!Number.isFinite(lengthSq) || lengthSq < 1e-12) {
            shouldRepair = true;
            invalidNormals = true;
            break;
          }
        }
      }

      if (!shouldRepair) {
        return;
      }

      geometry.computeVertexNormals();
      geometry.normalizeNormals();
      geometry.attributes.normal.needsUpdate = true;
      repairedMeshes += 1;

      if (!normalAttr) {
        repairedBecauseMissingNormals += 1;
      }
      if (invalidNormals) {
        repairedBecauseInvalidNormals += 1;
      }
    });

    return {
      repairedMeshes,
      repairedBecauseMissingNormals,
      repairedBecauseInvalidNormals,
    };
  };

  useEffect(() => {
    if (!mountRef.current) {
      return;
    }

    const mount = mountRef.current;
    const width = mount.clientWidth;
    const height = mount.clientHeight;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#edf2fb");
    sceneRef.current = scene;

    const camera = new THREE.PerspectiveCamera(50, width / height, 0.1, 1000);
    camera.position.set(7, 5, 7);
    camera.lookAt(0, 0, 0);
    cameraRef.current = camera;

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.25;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 3));
    mount.appendChild(renderer.domElement);
    rendererRef.current = renderer;
    logDiag("renderer:init", {
      toneMapping: renderer.toneMapping,
      toneMappingExposure: renderer.toneMappingExposure,
      outputColorSpace: renderer.outputColorSpace,
      pixelRatio: renderer.getPixelRatio(),
      shadowMapEnabled: renderer.shadowMap.enabled,
    });

    const composer = new EffectComposer(renderer);
    composer.setSize(width, height);
    const renderPass = new RenderPass(scene, camera);
    const bloomPass = new UnrealBloomPass(new THREE.Vector2(width, height), 0.18, 0.25, 1);
    composer.addPass(renderPass);
    composer.addPass(bloomPass);
    composerRef.current = composer;
    bloomPassRef.current = bloomPass;

    const pmremGenerator = new THREE.PMREMGenerator(renderer);
    const fallbackEnvironment = pmremGenerator.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environment = fallbackEnvironment;
    pmremGeneratorRef.current = pmremGenerator;
    environmentRef.current = fallbackEnvironment;
    logDiag("environment:fallback-applied", {
      mapping: fallbackEnvironment.mapping,
      hasEnvironment: Boolean(scene.environment),
    });

    void fetch("/hdr/studio_small_09_1k.hdr", { method: "HEAD" })
      .then((response) => {
        logDiag("environment:hdr-head", {
          ok: response.ok,
          status: response.status,
          contentType: response.headers.get("content-type"),
          contentLength: response.headers.get("content-length"),
        });
      })
      .catch((error: unknown) => {
        logDiag("environment:hdr-head-failed", error, "warn");
      });

    void import("three/examples/jsm/loaders/RGBELoader.js")
      .then((module) => {
        logDiag("environment:rgbe-imported", { moduleKeys: Object.keys(module) });
        const RGBE = module["RGBELoader"] as {
          new (): {
            load: (
              url: string,
              onLoad: (texture: THREE.DataTexture) => void,
              onProgress?: (event: ProgressEvent) => void,
              onError?: (event: unknown) => void
            ) => void;
          };
        };

        const hdrLoader = new RGBE();
        hdrLoader.load(
          "/hdr/studio_small_09_1k.hdr",
          (hdrTexture) => {
            if (sceneRef.current !== scene) {
              hdrTexture.dispose();
              return;
            }

            const envMap = pmremGenerator.fromEquirectangular(hdrTexture).texture;
            logDiag("environment:hdr-loaded", {
              textureType: hdrTexture.type,
              textureFormat: hdrTexture.format,
              textureColorSpace: hdrTexture.colorSpace,
            });
            hdrTexture.dispose();
            environmentRef.current?.dispose();
            environmentRef.current = envMap;
            scene.environment = envMap;
            logDiag("environment:hdr-applied", {
              mapping: envMap.mapping,
              hasEnvironment: Boolean(scene.environment),
            });
          },
          undefined,
          (error: unknown) => {
            logDiag("environment:hdr-load-failed", error, "warn");
            // Keep fallback environment if HDR is unavailable.
          }
        );
      })
      .catch((error: unknown) => {
        logDiag("environment:rgbe-import-failed", error, "warn");
        // Keep fallback environment if dynamic loader import fails.
      });

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.075;
    controls.minDistance = 2.5;
    controls.maxDistance = 100;
    controls.target.set(0, 0.5, 0);
    controlsRef.current = controls;

    const markInteracting = () => {
      isInteractingRef.current = true;
      currentRotationSpeedRef.current = 0;
    };

    const markInteractionEnd = () => {
      isInteractingRef.current = false;
    };

    controls.addEventListener("start", markInteracting);
    controls.addEventListener("end", markInteractionEnd);

    const key = new THREE.DirectionalLight("#fff8ee", 2.15);
    key.position.set(7, 10, 8);
    key.castShadow = true;
    key.shadow.mapSize.set(2048, 2048);
    key.shadow.bias = -0.00008;
    scene.add(key);

    const fill = new THREE.AmbientLight("#ffffff", 0.28);
    scene.add(fill);

    const rim = new THREE.DirectionalLight("#c8d9ff", 1.25);
    rim.position.set(-8, 3, -6);
    rim.castShadow = true;
    scene.add(rim);

    const top = new THREE.DirectionalLight("#ffffff", 0.68);
    top.position.set(0, 4, 14);
    scene.add(top);

    const hemi = new THREE.HemisphereLight("#f3f7ff", "#d7dbe4", 0.42);
    scene.add(hemi);

    const kick = new THREE.DirectionalLight("#ffd6c4", 0.65);
    kick.position.set(5, 2, -8);
    scene.add(kick);
    logDiag("lighting:configured", {
      key: { intensity: key.intensity, position: key.position.toArray() },
      fill: { intensity: fill.intensity },
      rim: { intensity: rim.intensity, position: rim.position.toArray() },
      top: { intensity: top.intensity, position: top.position.toArray() },
    });

    const modelRoot = new THREE.Group();
    scene.add(modelRoot);
    modelRootRef.current = modelRoot;
    loaderRef.current = new GLTFLoader();

    const animate = () => {
      controls.update();

      const now = performance.now();
      const deltaMs = lastFrameAtRef.current > 0 ? now - lastFrameAtRef.current : 16.7;
      const deltaFactor = Math.max(0.2, Math.min(3, deltaMs / 16.7));
      lastFrameAtRef.current = now;

      const modelRootNode = modelRootRef.current;
      if (modelRootNode) {
        const targetSpeed = isInteractingRef.current ? 0 : 0.015;
        const accelerationPerFrame = 0.015 / 60;

        if (currentRotationSpeedRef.current < targetSpeed) {
          currentRotationSpeedRef.current = Math.min(
            targetSpeed,
            currentRotationSpeedRef.current + accelerationPerFrame * deltaFactor
          );
        } else if (currentRotationSpeedRef.current > targetSpeed) {
          currentRotationSpeedRef.current = Math.max(
            targetSpeed,
            currentRotationSpeedRef.current - accelerationPerFrame * deltaFactor
          );
        }

        idleRotationYRef.current += currentRotationSpeedRef.current * deltaFactor;
        modelRootNode.rotation.y = idleRotationYRef.current;
      }

      if (bloomPassRef.current) {
        const t = now * 0.001;
        bloomPassRef.current.strength = 0.18 + Math.sin(t * 0.4) * 0.02;
      }

      composer.render();
      animationFrameRef.current = requestAnimationFrame(animate);
    };
    animate();

    const onResize = () => {
      const nextWidth = mount.clientWidth;
      const nextHeight = mount.clientHeight;
      renderer.setSize(nextWidth, nextHeight);
      camera.aspect = nextWidth / nextHeight;
      camera.updateProjectionMatrix();
      composer.setSize(nextWidth, nextHeight);
      bloomPass.setSize(nextWidth, nextHeight);
    };
    resizeHandlerRef.current = onResize;

    window.addEventListener("resize", onResize);

    return () => {
      activeLoadTokenRef.current += 1;
      cancelAnimationFrame(animationFrameRef.current);
      window.removeEventListener("resize", onResize);
      controls.removeEventListener("start", markInteracting);
      controls.removeEventListener("end", markInteractionEnd);
      controls.dispose();
      disposeObjectResources(activeRootRef.current);
      pmremGenerator.dispose();
      environmentRef.current?.dispose();
      composer.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === mount) {
        mount.removeChild(renderer.domElement);
      }

      activeRootRef.current = null;
      sceneRef.current = null;
      cameraRef.current = null;
      rendererRef.current = null;
      composerRef.current = null;
      bloomPassRef.current = null;
      controlsRef.current = null;
      modelRootRef.current = null;
      pmremGeneratorRef.current = null;
      environmentRef.current = null;
      loaderRef.current = null;
      resizeHandlerRef.current = null;
      hasAutoFramedRef.current = false;
      loadedRingIdRef.current = null;
      isInteractingRef.current = false;
      idleRotationYRef.current = 0;
      currentRotationSpeedRef.current = 0;
      lastFrameAtRef.current = 0;
    };
  }, []);

  useEffect(() => {
    ringParametersRef.current = ringParameters;
  }, [ringParameters]);

  useEffect(() => {
    const modelRoot = modelRootRef.current;
    const loader = loaderRef.current;
    if (!modelRoot || !loader) {
      return;
    }

    if (!modelUrl) {
      disposeObjectResources(activeRootRef.current);
      modelRoot.clear();
      activeRootRef.current = null;
      hasAutoFramedRef.current = false;
      loadedRingIdRef.current = null;
      return;
    }

    const loadToken = ++activeLoadTokenRef.current;
    const incomingRingId = parseRingIdFromModelUrl(modelUrl);

    loader.load(
      modelUrl,
      (gltf) => {
        if (loadToken !== activeLoadTokenRef.current) {
          disposeObjectResources(gltf.scene);
          return;
        }

        disposeObjectResources(activeRootRef.current);
        modelRoot.clear();

        const modelDiagnosticsBeforeRepair = inspectModelGeometry(gltf.scene);
        const repairDiagnostics = repairGeometryForShading(gltf.scene);
        const modelDiagnosticsAfterRepair = inspectModelGeometry(gltf.scene);
        logDiag("model:loaded", {
          url: modelUrl,
          ringId: incomingRingId,
          diagnosticsBeforeRepair: modelDiagnosticsBeforeRepair,
          repairDiagnostics,
          diagnosticsAfterRepair: modelDiagnosticsAfterRepair,
          hasEnvironment: Boolean(sceneRef.current?.environment),
        });

        const materialDiagnostics = applyMaterials(gltf.scene, ringParametersRef.current);
        logDiag("materials:applied", {
          params: ringParametersRef.current,
          diagnostics: materialDiagnostics,
        });

        if (materialDiagnostics.gemLikeMeshes === materialDiagnostics.totalMeshes && materialDiagnostics.totalMeshes > 1) {
          logDiag("materials:suspicious-all-gem", materialDiagnostics, "warn");
        }
        if (!sceneRef.current?.environment) {
          logDiag("environment:missing-after-model-load", { modelUrl }, "warn");
        }

        modelRoot.add(gltf.scene);
        activeRootRef.current = gltf.scene;

        const shouldResetView = !hasAutoFramedRef.current || incomingRingId !== loadedRingIdRef.current;
        if (shouldResetView) {
          idleRotationYRef.current = 0;
          currentRotationSpeedRef.current = 0;
          lastFrameAtRef.current = 0;
          if (modelRootRef.current) {
            modelRootRef.current.rotation.y = 0;
          }
          fitCameraToObject(gltf.scene);
          hasAutoFramedRef.current = true;
        }
        loadedRingIdRef.current = incomingRingId;
      },
      undefined,
      (error: unknown) => {
        if (loadToken !== activeLoadTokenRef.current) {
          return;
        }
        logDiag("model:load-failed", { url: modelUrl, error }, "error");
        disposeObjectResources(activeRootRef.current);
        modelRoot.clear();
        activeRootRef.current = null;
      }
    );
  }, [modelUrl]);

  useEffect(() => {
    if (!activeRootRef.current) {
      return;
    }
    const materialDiagnostics = applyMaterials(activeRootRef.current, ringParameters);
    logDiag("materials:reapplied", {
      params: ringParameters,
      diagnostics: materialDiagnostics,
      hasEnvironment: Boolean(sceneRef.current?.environment),
      exposure: rendererRef.current?.toneMappingExposure,
    });
  }, [ringParameters]);

  return (
    <div className="viewer-canvas-shell">
      <div className="viewer-canvas" ref={mountRef} />
      {ringSummary ? (
        <>
          <div className="viewer-overlay viewer-overlay-price">
            <span className="viewer-overlay-label">Estimated Price</span>
            <strong>${ringSummary.estimatedPriceUsd.toFixed(2)}</strong>
          </div>
          {ringSummary.manufacturabilityWarnings.length > 0 ? (
            <div className="viewer-overlay viewer-overlay-warnings" role="status" aria-live="polite">
              {ringSummary.manufacturabilityWarnings.map((warning) => (
                <p key={warning.code}>{warning.message}</p>
              ))}
            </div>
          ) : null}
        </>
      ) : null}
    </div>
  );
}
