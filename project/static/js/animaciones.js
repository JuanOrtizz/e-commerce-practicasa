gsap.registerPlugin(ScrollTrigger)

document.addEventListener("DOMContentLoaded", () => {

    if (gsap.utils.toArray(".animacion-caida-y").length) {
        gsap.fromTo(".animacion-caida-y",
        {
            y: -40,
        },
        {
            y: 0,
            rotation: 360,       // Gira 360 grados
            duration: 1,         // Tarda 2 segundos
            ease: "bounce.out",   // Efecto de rebote al final
            scrollTrigger: {
                trigger: ".animacion-caida-y",
                start: "top 95%",
            }
        })
    }

    if (gsap.utils.toArray(".animacion-aparicion-escalada").length) {
        gsap.fromTo(".animacion-aparicion-escalada",
        {
            scale: 0.1,
            opacity: 0
        },
        {
            scale: 1,
            opacity: 1,
            duration: 1,
            scrollTrigger: {
                trigger: ".animacion-aparicion-escalada",
                start: "top 95%",
            }
        })
    }

    ScrollTrigger.create({
        start: "300px top",
        onEnter: () => document.getElementById("btnSubir").classList.add("visible"),
        onLeaveBack: () => document.getElementById("btnSubir").classList.remove("visible")
    })

    document.getElementById("btnSubir").addEventListener("click", () => {
        window.scrollTo({ top: 0, behavior: "smooth" })
    })

    if (gsap.utils.toArray(".animacion-aparicion-abajo-fade").length) {
        gsap.fromTo(".animacion-aparicion-abajo-fade",
            {
                y: 60,
                opacity: 0
            },
            {
                y: 0,
                opacity: 1,
                duration: 1,
                ease: "power3.out"
             }
        )
    }

})