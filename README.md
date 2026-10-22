# 🎮 Game Lingo Overlay

**Game Lingo Overlay** es una aplicación híbrida diseñada para traducir bloques de texto en videojuegos (como *Hollow Knight*) en tiempo real, enfocada específicamente en el **aprendizaje interactivo de inglés** sin arruinar la inmersión del juego.

---

## 🏗️ Arquitectura Híbrida (`Backend Python` + `Web Overlay Moderno`)

1. **Backend en Python (`FastAPI` + `WebSockets`)**:
   - **Captura de Pantalla Ultrarrápida (`mss`)**: Captura únicamente la región configurada para los cuadros de diálogo del juego.
   - **Motor OCR (`RapidOCR` / `EasyOCR` / `Tesseract`)**: Extrae el bloque de texto en inglés con preprocesamiento de alto contraste ideal para fuentes estilizadas de videojuegos.
   - **Motor Lingüístico e IA (`deep-translator` / `LLM`)**:
     - Tokenización y traducción **palabra por palabra** según su contexto.
     - Traducción completa de la oración (oculta por defecto para fomentar el aprendizaje activo).
     - Detección de nivel de dificultad y modismos (*lore* / inglés poético).

2. **Frontend / Overlay Web Moderno (`HTML/CSS/JS` o `React` sobre ventana transparente `pywebview` / `Electron`)**:
   - **Modo Aprendizaje Interactivo**:
     - **Palabras Interactivas (Hover/Click)**: Al pasar el cursor sobre cualquier palabra en inglés detectada, muestra una tarjeta flotante con su traducción exacta, categoría gramatical y sinónimos.
     - **Traducción Completa "Spoiler-Free" (Blur/Reveal)**: La traducción completa del bloque aparece difuminada u oculta; solo se revela al hacer clic o presionar un atajo si necesitas confirmar el sentido completo de la oración.
   - **Personalización Total**:
     - **Temas Visuales**: Tema *Hallownest / Void* (inspirado en *Hollow Knight*), tema *Minimal Dark*, y tema *Glassmorphism*.
     - **Ajustes de Interfaz**: Opacidad del fondo, tamaño de fuente, color de resaltado según dificultad de palabra, y posición libre en pantalla.
     - **Atajos Personalizables**: Captura bajo demanda con tecla rápida (ej. `Alt + T`) o modo observador automático.

---

## 🚀 Hoja de Ruta (Roadmap)

- [x] **Fase 0**: Creación del repositorio y diseño de arquitectura híbrida.
- [ ] **Fase 1 (MVP Core)**:
  - Backend en Python con captura de región en pantalla, OCR y API de desglose palabra por palabra + traducción completa.
  - Interfaz Web Overlay interactiva con modo *Hover Word-by-Word*, botón *Reveal Full Translation* y selector de región.
- [ ] **Fase 2 (Personalización)**:
  - Selector de temas (*Hollow Knight Void Theme*, opacidad, tipografías, atajos de teclado).
- [ ] **Fase 3 (Expansión)**:
  - Guardado de vocabulario local ("Hunter's Lexicon") y pronunciación TTS.
