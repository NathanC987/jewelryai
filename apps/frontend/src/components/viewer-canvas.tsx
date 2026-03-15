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
      gold: "#d9b45a",
      rose_gold: "#c98a7a",
      platinum: "#d9dee4",
      silver: "#c7ced7",
    };
    const gemPalette: Record<string, string> = {
      diamond: "#d5e8ff",
      ruby: "#c53946",
      emerald: "#2f9f62",
      sapphire: "#3558c9",
    };

    const applyMaterials = (root: THREE.Object3D) => {
      const metalColor = new THREE.Color(metalPalette[ringParameters?.metal ?? "gold"]);
      const gemColor = new THREE.Color(gemPalette[ringParameters?.gemstone_type ?? "diamond"]);

      const classifyGemLike = (node: THREE.Mesh, source?: THREE.Material): boolean => {
        const meshName = node.name ?? "";
        const materialName = source?.name ?? "";

        const pathHints: string[] = [];
        let cursor: THREE.Object3D | null = node;
        while (cursor) {
          pathHints.push(cursor.name ?? "");
          cursor = cursor.parent;
        }

        const hint = `${meshName} ${materialName} ${pathHints.join(" ")}`.toLowerCase();
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
        const base = source?.clone() as THREE.MeshPhysicalMaterial | undefined;
        const gemMaterial =
          base instanceof THREE.MeshPhysicalMaterial
            ? base
            : new THREE.MeshPhysicalMaterial();

        gemMaterial.name = source?.name ?? gemMaterial.name;
        gemMaterial.map = null;
        gemMaterial.roughnessMap = null;
        gemMaterial.metalnessMap = null;
        gemMaterial.normalMap = null;
        gemMaterial.aoMap = null;
        gemMaterial.emissiveMap = null;
        gemMaterial.transmissionMap = null;
        gemMaterial.thicknessMap = null;
        gemMaterial.clearcoatMap = null;
        gemMaterial.clearcoatRoughnessMap = null;
        gemMaterial.specularIntensityMap = null;
        gemMaterial.color = gemColor.clone();
        gemMaterial.metalness = 0.0;
        gemMaterial.roughness = 0.0;
        gemMaterial.transmission = 1.0;
        gemMaterial.thickness = Math.max(gemMaterial.thickness ?? 0.0, 1.8);
        gemMaterial.ior = Math.max(gemMaterial.ior ?? 1.0, 2.2);
        gemMaterial.clearcoat = 1.0;
        gemMaterial.clearcoatRoughness = 0.0;
        gemMaterial.reflectivity = 1.0;
        gemMaterial.specularIntensity = 1.0;
        gemMaterial.envMapIntensity = 2.8;
        return gemMaterial;
      };

      const buildMetalMaterial = (source?: THREE.Material) => {
        const base = source?.clone() as THREE.MeshPhysicalMaterial | undefined;
        const metalMaterial =
          base instanceof THREE.MeshPhysicalMaterial
            ? base
            : new THREE.MeshPhysicalMaterial();

        metalMaterial.name = source?.name ?? metalMaterial.name;
        metalMaterial.map = null;
        metalMaterial.roughnessMap = null;
        metalMaterial.metalnessMap = null;
        metalMaterial.normalMap = null;
        metalMaterial.aoMap = null;
        metalMaterial.emissiveMap = null;
        metalMaterial.clearcoatMap = null;
        metalMaterial.clearcoatRoughnessMap = null;
        metalMaterial.specularIntensityMap = null;
        metalMaterial.color = metalColor.clone();
        metalMaterial.metalness = 1.0;
        metalMaterial.roughness = 0.09;
        metalMaterial.clearcoat = 1.0;
        metalMaterial.clearcoatRoughness = 0.03;
        metalMaterial.reflectivity = 1.0;
        metalMaterial.specularIntensity = 1.0;
        metalMaterial.envMapIntensity = 2.2;
        metalMaterial.transmission = 0.0;
        return metalMaterial;
      };

      root.traverse((node) => {
        if (!(node instanceof THREE.Mesh)) {
          return;
        }

        if (Array.isArray(node.material)) {
          node.material = node.material.map((sourceMaterial) => {
            const isGemLike = classifyGemLike(node, sourceMaterial);
            return isGemLike ? buildGemMaterial(sourceMaterial) : buildMetalMaterial(sourceMaterial);
          });
        } else {
          const isGemLike = classifyGemLike(node, node.material ?? undefined);
          node.material = isGemLike
            ? buildGemMaterial(node.material ?? undefined)
            : buildMetalMaterial(node.material ?? undefined);
        }

        node.castShadow = true;
        node.receiveShadow = true;
      });
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
