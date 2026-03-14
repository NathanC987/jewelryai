"use client";

import { useEffect, useRef } from "react";
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { OrbitControls } from "three/examples/jsm/controls/OrbitControls.js";

type ViewerCanvasProps = {
  modelUrl: string | null;
};

export function ViewerCanvas({ modelUrl }: ViewerCanvasProps) {
  const mountRef = useRef<HTMLDivElement | null>(null);

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
    renderer.setSize(width, height);
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    mount.appendChild(renderer.domElement);

    const controls = new OrbitControls(camera, renderer.domElement);
    controls.enableDamping = true;
    controls.dampingFactor = 0.08;
    controls.minDistance = 2.5;
    controls.maxDistance = 30;
    controls.target.set(0, 0.5, 0);

    const key = new THREE.DirectionalLight("#fff2d9", 1.1);
    key.position.set(7, 10, 8);
    scene.add(key);

    const fill = new THREE.AmbientLight("#fffdf6", 0.85);
    scene.add(fill);

    const rim = new THREE.DirectionalLight("#e8d8bc", 0.45);
    rim.position.set(-8, 3, -6);
    scene.add(rim);

    const modelRoot = new THREE.Group();
    scene.add(modelRoot);

    const placeholder = new THREE.Group();
    const ringGeometry = new THREE.TorusGeometry(2, 0.5, 32, 120);
    const ringMaterial = new THREE.MeshStandardMaterial({
      color: "#d8b158",
      metalness: 0.85,
      roughness: 0.2,
    });
    const ringMesh = new THREE.Mesh(ringGeometry, ringMaterial);
    placeholder.add(ringMesh);

    const stoneGeometry = new THREE.OctahedronGeometry(0.8, 1);
    const stoneMaterial = new THREE.MeshPhysicalMaterial({
      color: "#9ec7ff",
      transmission: 1,
      thickness: 0.8,
      roughness: 0,
      ior: 2.1,
    });
    const stoneMesh = new THREE.Mesh(stoneGeometry, stoneMaterial);
    stoneMesh.position.set(0, 2.2, 0);
    placeholder.add(stoneMesh);
    modelRoot.add(placeholder);

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

    if (modelUrl) {
      const loader = new GLTFLoader();
      loader.load(
        modelUrl,
        (gltf) => {
          modelRoot.clear();
          modelRoot.add(gltf.scene);
          fitCameraToObject(gltf.scene);
        },
        undefined,
        () => {
          modelRoot.clear();
          modelRoot.add(placeholder);
        }
      );
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
      ringGeometry.dispose();
      ringMaterial.dispose();
      stoneGeometry.dispose();
      stoneMaterial.dispose();
      renderer.dispose();
      if (renderer.domElement.parentNode === mount) {
        mount.removeChild(renderer.domElement);
      }
    };
  }, [modelUrl]);

  return <div className="viewer-canvas" ref={mountRef} />;
}
