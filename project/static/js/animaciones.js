document.addEventListener("DOMContentLoaded", () => {

    gsap.fromTo(".animacion-caida-y",
    {
        y: -40,
    },
    {
        y: 0,
        rotation: 360,       // Gira 360 grados
        duration: 1,         // Tarda 2 segundos
        ease: "bounce.out"   // Efecto de rebote al final
    });

    gsap.fromTo(".animacion-aparicion-escalada",
    {
        scale: 0.1,
        opacity: 0
    },
    {
        scale: 1,
        opacity: 1,
        duration: 1,         // Tarda 2 segundos
    });

    gsap.to(".animacion-escribir",
    {
        typewriter: {
            speed: 0.05, // Velocidad de escritura (en segundos por carácter)
            cursor: "|", // Cursor que se muestra mientras se escribe
        },
        duration: 2, // Duración total de la animación (ajusta según el texto)
    })
});

