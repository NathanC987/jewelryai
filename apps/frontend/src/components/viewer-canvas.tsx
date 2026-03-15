"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";
import { RoomEnvironment } from "three/examples/jsm/environments/RoomEnvironment.js";

type ViewerCanvasProps = {
  modelUrl: string | null;
  ringParameters: {
    metal: "gold" | "rose_gold" | "platinum" | "silver";
    gemstone_type: "diamond" | "ruby" | "emerald" | "sapphire";
  } | null;
};

export function ViewerCanvas({ modelUrl, ringParameters }: ViewerCanvasProps) {
  const mountRef = useRef<HTMLDivElement | null>(null);
  const activeRootRef = useRef<THREE.Object3D | null>(null);

  useEffect(() => {
    if (!mountRef.current) {
      return;
    }

    const mount = mountRef.current;
    const width = mount.clientWidth;
    const height = mount.clientHeight;

    const scene = new THREE.Scene();
    scene.background = new THREE.Color("#f3f5fb");

    const camera = new THREE.PerspectiveCamera(55, width / height, 0.1, 1000);
    camera.position.set(7, 5, 7);
    camera.lookAt(0, 0, 0);

    const renderer = new THREE.WebGLRenderer({ antialias: true });
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = 1.3;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 3));
    mount.appendChild(renderer.domElement);

    const pmremGenerator = new THREE.PMREMGenerator(renderer);
    const environment = pmremGenerator.fromScene(new RoomEnvironment(), 0.04).texture;
    scene.environment = environment;

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.minDistance = 2.5;
    controls.maxDistance = 30;
    controls.target.set(0, 0.5, 0);

    const key = new THREE.DirectionalLight("#fff2d9", 2.2);
    key.position.set(7, 10, 8);
    key.castShadow = true;
    scene.add(key);

    const fill = new THREE.AmbientLight("#fffdf6", 0.65);
    scene.add(fill);

    const rim = new THREE.DirectionalLight("#e8d8bc", 0.9);
    rim.position.set(-8, 3, -6);
    rim.castShadow = true;
    scene.add(rim);

    const top = new THREE.DirectionalLight("#f7f7ff", 1.1);
    top.position.set(0, 4, 14);
    scene.add(top);

    const modelRoot = new THREE.Group();
    scene.add(modelRoot);

    const fitCameraToObject = (object: THREE.Object3D) => {
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

    const applyMaterials = (root: THREE.Object3D) => {
      const metalColor = new THREE.Color(metalPalette[ringParameters?.metal ?? "gold"]);
      const gemColor = new THREE.Color(gemPalette[ringParameters?.gemstone_type ?? "diamond"]);

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

        if (source instanceof THREE.MeshPhysicalMaterial) {
          if (source.transmission > 0.35 || source.ior > 1.5) {
            return true;
          }
        }

        return false;
      };

      const buildGemMaterial = (source?: THREE.Material) => {
        const gemstoneType = ringParameters?.gemstone_type ?? "diamond";
        const isDiamond = gemstoneType === "diamond";

        if (!isDiamond) {
          const gemMaterial = new THREE.MeshStandardMaterial();
          gemMaterial.name = source?.name ?? "gemstone";
          gemMaterial.vertexColors = false;
          gemMaterial.color = gemColor.clone();
          gemMaterial.emissive = gemColor.clone().multiplyScalar(0.28);
          gemMaterial.metalness = 0.0;
          gemMaterial.roughness = 0.28;
          gemMaterial.envMapIntensity = 1.4;
          gemMaterial.needsUpdate = true;
          return gemMaterial;
        }

        const base = source?.clone() as THREE.MeshPhysicalMaterial | undefined;
        const gemMaterial =
          base instanceof THREE.MeshPhysicalMaterial
            ? base
            : new THREE.MeshPhysicalMaterial();

        gemMaterial.name = source?.name ?? gemMaterial.name;
        // Ignore baked per-vertex colors that can force black/white output.
        gemMaterial.vertexColors = false;
        gemMaterial.color = gemColor.clone();
        gemMaterial.emissive = gemColor.clone().multiplyScalar(0.02);
        gemMaterial.metalness = 0.0;
        gemMaterial.roughness = 0.05;
        gemMaterial.transmission = 0.98;
        gemMaterial.thickness = Math.max(gemMaterial.thickness ?? 0.0, 0.8);
        gemMaterial.ior = Math.max(gemMaterial.ior ?? 1.0, 2.2);
        gemMaterial.clearcoat = 1.0;
        gemMaterial.clearcoatRoughness = 0.0;
        gemMaterial.reflectivity = 1.0;
        gemMaterial.specularIntensity = 1.0;
        gemMaterial.envMapIntensity = 3.1;
        gemMaterial.attenuationDistance = 2.2;
        gemMaterial.attenuationColor = gemColor.clone();
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
        // Ignore baked per-vertex colors that can force black/white output.
        metalMaterial.vertexColors = false;
        metalMaterial.color = metalColor.clone();
        metalMaterial.emissive = new THREE.Color("#000000");
        metalMaterial.metalness = 1.0;
        metalMaterial.roughness = 0.2;
        metalMaterial.clearcoat = 0.6;
        metalMaterial.clearcoatRoughness = 0.1;
        metalMaterial.reflectivity = 1.0;
        metalMaterial.specularIntensity = 1.0;
        metalMaterial.envMapIntensity = 2.7;
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

      // If only a tiny subset was detected as gem-like, gemstone swaps are visually invisible.
      // Promote all setting meshes so gemstone customization always shows a clear color change.
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

      // Fallback: if naming/material hints fail, treat all setting meshes as gemstone.
      if (gemLikeMeshes.size === 0 && meshes.length > 0) {
        if (settingMeshes.length > 0) {
          for (const mesh of settingMeshes) {
            gemLikeMeshes.add(mesh);
          }
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
          }
        }
      }

      console.info("[viewer] material-assign", {
        gemstoneType: ringParameters?.gemstone_type,
        metalType: ringParameters?.metal,
        meshCount: meshes.length,
        settingMeshCount: settingMeshes.length,
        gemMeshCount: gemLikeMeshes.size,
        meshSummary: meshes.map((mesh) => {
          const source = Array.isArray(mesh.material) ? mesh.material[0] : mesh.material;
          const box = new THREE.Box3().setFromObject(mesh);
          const size = box.getSize(new THREE.Vector3());
          return {
            name: mesh.name,
            verts: mesh.geometry.attributes.position.count,
            isGemLike: gemLikeMeshes.has(mesh),
            size: [
              Number(size.x.toFixed(3)),
              Number(size.y.toFixed(3)),
              Number(size.z.toFixed(3)),
            ],
            hint: buildHint(mesh, source ?? undefined),
          };
        }),
      });

      for (const mesh of meshes) {
        const isGemLike = gemLikeMeshes.has(mesh);
        if (Array.isArray(mesh.material)) {
          mesh.material = mesh.material.map((sourceMaterial) =>
            isGemLike ? buildGemMaterial(sourceMaterial) : buildMetalMaterial(sourceMaterial)
          );
        } else {
          mesh.material = isGemLike
            ? buildGemMaterial(mesh.material ?? undefined)
            : buildMetalMaterial(mesh.material ?? undefined);
        }
        mesh.castShadow = true;
        mesh.receiveShadow = true;
      }
    };

    if (modelUrl) {
      const loader = new GLTFLoader();
      loader.load(
        modelUrl,
        (gltf) => {
          modelRoot.clear();
          applyMaterials(gltf.scene);
          modelRoot.add(gltf.scene);
          activeRootRef.current = gltf.scene;
          fitCameraToObject(gltf.scene);
        },
        undefined,
        () => {
          modelRoot.clear();
          activeRootRef.current = null;
        }
      );
    } else {
      modelRoot.clear();
      activeRootRef.current = null;
    }

    let frameId = 0;
    const animate = () => {
      controls.update();
      renderer.render(scene, camera);
      frameId = requestAnimationFrame(animate);
    };
    animate();

    const onResize = () => {
      const nextWidth = mount.clientWidth;
      const nextHeight = mount.clientHeight;
      renderer.setSize(nextWidth, nextHeight);
      camera.aspect = nextWidth / nextHeight;
      camera.updateProjectionMatrix();
    };

    window.addEventListener("resize", onResize);

    return () => {
      cancelAnimationFrame(frameId);
      window.removeEventListener("resize", onResize);
      controls.dispose();
      if (activeRootRef.current) {
        activeRootRef.current.traverse((node) => {
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
      }
      pmremGenerator.dispose();
      environment.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === mount) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, [modelUrl, ringParameters]);

  return <div className="viewer-canvas" ref={mountRef} />;
}
