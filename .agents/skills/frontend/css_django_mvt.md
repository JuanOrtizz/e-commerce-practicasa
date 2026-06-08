# CSS Django MVT - Reglas para el agente

## Cuándo crear
- `globalStyles.css` para estilos globales del proyecto
- `app.css` para estilos específicos de cada app

## Reglas

### 1. Variables CSS globales (globalStyles.css)
- Definir paleta con `--primary-color`, `--secondary-color`, `--tertiary-color`
- También sus variantes hover: `--primary-color-hover`, etc.
- Usar formato HEX (#00CCFF)

### 2. Layout base
- `body`: `display: flex; flex-direction: column; min-height: 100dvh`
- `main`: `flex: 1` para ocupar espacio vertical disponible
- `header` y `footer`: color de fondo con variable primary

### 3. Estilos por app
- Prefijo de clases específico de la app: `.tabla-principal th`, `.card-personalizada`
- Hover en filas: `background-color: var(--tertiary-color-hover)`
- No repetir estilos que Bootstrap ya cubre

### 4. Bootstrap primero
- Usar clases Bootstrap para layout, botones, formularios
- CSS propio solo para lo que Bootstrap no ofrece (colores personalizados, hover, animaciones)

## Ejemplo genérico

```css
/* static/css/globalStyles.css */
:root {
    --primary-color: #00CCFF;
    --secondary-color: #3399FF;
    --tertiary-color: #66FFFF;
    --primary-color-hover: #0066FF;
    --secondary-color-hover: #3366CC;
    --tertiary-color-hover: #99FFFF;
}

body {
    font-family: 'Roboto', sans-serif;
    display: flex;
    flex-direction: column;
    min-height: 100dvh;
    margin: 0;
}

main { flex: 1; }

header { background-color: var(--primary-color); }

footer {
    background-color: var(--primary-color);
    display: flex;
    justify-content: center;
}
```
