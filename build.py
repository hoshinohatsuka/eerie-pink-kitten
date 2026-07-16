import PyInstaller.__main__
import os

if __name__ == '__main__':
    target_dir = r"H:\My-soft\vibe-projects\Live2Dpet\测试"
    
    # Ensure the target directory exists
    os.makedirs(target_dir, exist_ok=True)
    
    PyInstaller.__main__.run([
        'main.py',
        '--name=Live2Dpet',
        '--onedir',
        '--windowed',
        '--noconfirm',
        '--clean',
        f'--distpath={target_dir}',
        '--hidden-import=win32com',
        '--hidden-import=win32com.client',
        '--hidden-import=win32com.shell',
        '--hidden-import=winshell',
        '--hidden-import=pylnk3'
    ])
    
    print(f"Build completed! The application should be located in {target_dir}\\Live2Dpet")
