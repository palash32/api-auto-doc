"use client";

import { useLayoutEffect } from "react";
import gsap from "gsap";
import { ScrollTrigger } from "gsap/ScrollTrigger";
import { Flip } from "gsap/Flip";
import { Draggable } from "gsap/Draggable";

export const GsapRegistry = () => {
    useLayoutEffect(() => {
        gsap.registerPlugin(ScrollTrigger, Flip, Draggable);

        // Set default ease
        gsap.defaults({ ease: "power3.out" });
    }, []);

    return null;
};
