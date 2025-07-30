import os
import shutil
import PyInstaller.__main__

# === CLEAN OLD BUILDS ===
shutil.rmtree("build", ignore_errors=True)
shutil.rmtree("dist", ignore_errors=True)

# === SETUP LOCAL BROWSER PATH ===
browser_path = "venv/lib/python3.11/site-packages/playwright/.local-browsers"

if not os.path.exists(browser_path):
    raise FileNotFoundError(f"Playwright browsers not found at: {browser_path}")

# === BUILD EXE ===
PyInstaller.__main__.run([
    'main.py',
    '--name=FBMBot',
    '--onefile',
    '--noconfirm',
    '--windowed',  # remove if you want terminal
    f'--add-data=ui:ui',
    f'--add-data=auth:auth',
    f'--add-data=automation:automation',
    f'--add-data=database:database',
    f'--add-data={browser_path}:playwright/.local-browsers',
    '--distpath=app',  # Save exe in app/
])
