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

    const btnSubir = document.getElementById("btnSubir")
    gsap.set(btnSubir, { autoAlpha: 0, scale: 0.8 })

    ScrollTrigger.create({
        start: "300px top",
        onEnter: () => gsap.to(btnSubir, { autoAlpha: 1, scale: 1, duration: 0.3, ease: "power2.out" }),
        onLeaveBack: () => gsap.to(btnSubir, { autoAlpha: 0, scale: 0.8, duration: 0.3, ease: "power2.in" })
    })

    btnSubir.addEventListener("click", () => {
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

    gsap.utils.toArray(".fila-categorias").forEach((fila) => {
        const cards = fila.querySelectorAll(".animacion-card")
        if (!cards.length) return
        gsap.fromTo(cards,
            { y: 60, opacity: 0 },
            {
                y: 0,
                opacity: 1,
                duration: 0.7,
                ease: "power3.out",
                stagger: 0.08,
                scrollTrigger: {
                    trigger: fila,
                    start: "top 85%",
                    once: true
                }
            })
    })

    gsap.utils.toArray(".animacion-titulo").forEach((titulo) => {
        gsap.fromTo(titulo,
            { y: 30, opacity: 0 },
            {
                y: 0,
                opacity: 1,
                duration: 0.6,
                ease: "power2.out",
                scrollTrigger: {
                    trigger: titulo,
                    start: "top 90%",
                    once: true
                }
            })
    })

    const trustItems = gsap.utils.toArray(".animacion-trust")
    if (trustItems.length) {
        gsap.fromTo(trustItems,
            { y: 40, opacity: 0 },
            {
                y: 0,
                opacity: 1,
                duration: 0.7,
                ease: "power3.out",
                stagger: 0.15,
                scrollTrigger: {
                    trigger: trustItems[0],
                    start: "top 85%",
                    once: true
                }
            })
    }

    const carouselHero = document.getElementById("carouselHero")
    if (carouselHero) {
        const animarSlide = () => {
            const imagen = carouselHero.querySelector(".carousel-item.active .hero-slide")
            if (!imagen) return
            gsap.fromTo(imagen,
                { scale: 1.05 },
                { scale: 1.2, duration: 3, ease: "power1.out", overwrite: true })
        }
        carouselHero.addEventListener("slid.bs.carousel", animarSlide)
        animarSlide()
    }

})