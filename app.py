<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Eternit - Gestión Profesional</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://unpkg.com/lucide@latest"></script>
    <style>
        :root {
            --color-rojo: #E30613;
            --color-rojo-dark: #b3050f;
            --color-fondo: #f8fafc;
            --color-tarjeta: #ffffff;
            --color-texto-p: #1e293b;
            --color-texto-s: #64748b;
            --borde-suave: #e2e8f0;
            --shadow: 0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1);
        }

        body {
            font-family: 'Inter', sans-serif;
            background-color: var(--color-fondo);
            color: var(--color-texto-p);
            margin: 0;
            display: flex;
            justify-content: center;
            min-height: 100vh;
        }

        .container {
            max-width: 1100px;
            width: 90%;
            margin: 60px 0;
        }

        /* --- HEADER PROFESIONAL --- */
        header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 50px;
            padding-bottom: 25px;
            border-bottom: 1px solid var(--borde-suave);
        }

        .brand-box {
            display: flex;
            align-items: center;
            gap: 15px;
        }

        .logo-eternit {
            height: 45px; /* Logo nítido */
        }

        h1 {
            font-size: 24px;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin: 0;
        }

        h1 span {
            color: var(--color-rojo);
        }

        /* --- GRID DE ACCIONES --- */
        .grid-buttons {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
            gap: 25px;
        }

        .btn-card {
            background-color: var(--color-tarjeta);
            border: 1px solid var(--borde-suave);
            border-radius: 12px;
            padding: 30px;
            text-decoration: none;
            display: flex;
            flex-direction: column;
            align-items: flex-start; /* Alineación moderna a la izquierda */
            transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: var(--shadow);
        }

        .btn-card:hover {
            transform: translateY(-5px);
            border-color: var(--color-rojo);
            box-shadow: 0 20px 25px -5px rgb(0 0 0 / 0.1);
        }

        .icon-box {
            width: 48px;
            height: 48px;
            background-color: #fef2f2;
            color: var(--color-rojo);
            display: flex;
            align-items: center;
            justify-content: center;
            border-radius: 10px;
            margin-bottom: 20px;
            transition: background-color 0.3s;
        }

        .btn-card:hover .icon-box {
            background-color: var(--color-rojo);
            color: white;
        }

        .btn-card span {
            font-weight: 600;
            font-size: 16px;
            color: var(--color-texto-p);
            margin-bottom: 8px;
        }

        .btn-card p {
            font-size: 13px;
            color: var(--color-texto-s);
            margin: 0;
            line-height: 1.5;
        }

        /* --- BOTÓN DE ACCIÓN DESTACADO --- */
        .btn-card.featured {
            background-color: var(--color-rojo);
            border: none;
        }

        .btn-card.featured .icon-box {
            background-color: rgba(255,255,255,0.2);
            color: white;
        }

        .btn-card.featured span, .btn-card.featured p {
            color: white;
        }

        .btn-card.featured:hover {
            background-color: var(--color-rojo-dark);
        }

        /* --- FOOTER --- */
        footer {
            margin-top: 80px;
            text-align: center;
            color: var(--color-texto-s);
            font-size: 13px;
        }
    </style>
</head>
<body>

    <div class="container">
        <header>
            <div class="brand-box">
                <img src="https://eternit.com.co/sites/default/files/LOGO-ETERNIT-COLOR.svg" alt="Eternit Logo" class="logo-eternit">
                <h1>Gestión <span>Eternit</span></h1>
            </div>
            <div style="color: var(--color-texto-s); font-size: 14px; font-weight: 500;">
                Bienvenido, Administrador
            </div>
        </header>

        <div class="grid-buttons">
            <a href="#" class="btn-card">
                <div class="icon-box"><i data-lucide="bar-chart-3"></i></div>
                <span>REPORTES</span>
                <p>Visualiza el rendimiento y estadísticas mensuales de proyectos.</p>
            </a>

            <a href="#" class="btn-card">
                <div class="icon-box"><i data-lucide="package"></i></div>
                <span>INVENTARIO</span>
                <p>Control de existencias y pedidos de materiales en tiempo real.</p>
            </a>

            <a href="#" class="btn-card featured">
                <div class="icon-box"><i data-lucide="plus-circle"></i></div>
                <span>NUEVO PROYECTO</span>
                <p>Inicia una nueva orden de trabajo con parámetros técnicos.</p>
            </a>

            <a href="#" class="btn-card">
                <div class="icon-box"><i data-lucide="wrench"></i></div>
                <span>SOPORTE TÉCNICO</span>
                <p>Asistencia especializada para incidencias en obra.</p>
            </a>
        </div>

        <footer>
            © 2026 Eternit Colombia · Sistema Central de Operaciones · <strong>Calidad Profesional</strong>
        </footer>
    </div>

    <script>
        // Inicializa los iconos de Lucide
        lucide.createIcons();
    </script>
</body>
</html>
