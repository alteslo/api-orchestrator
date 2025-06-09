from datetime import datetime
from pathlib import Path
import subprocess
import os
import shutil
from multiprocessing import Pool

ROOT_DIR = "app/src"
ROOT_COMPILE_DIR = "./compiled"

def compile_module_to_pyc(module: Path):        
    try:
        modules_no_compile = ("main", "alembic", "env")
        if len([module_no_compile for module_no_compile in modules_no_compile if module_no_compile in str(module)]) > 0:
            return
        module_path_name, module_file_name = os.path.split(module)
        command = f"python -OO -m py_compile {module}"
        result = subprocess.run(command, shell=True, encoding='utf-8', capture_output=True, text=False, check=True)
        print(f".", end="")
        compile_files = next(os.walk(Path(f"{module_path_name}/__pycache__")))[2]
        compile_file = [compile_file for compile_file in compile_files if module.name.split(".")[0] in compile_file][0]
        new_compile_file_name = f'{compile_file.split(".")[0]}.pyc'
        src_path = Path.joinpath(Path(f"{module_path_name}/__pycache__"), compile_file)
        dst_path = Path.joinpath(Path(module_path_name), new_compile_file_name)
        # print(f"Moved compiled module: '{compile_file}' to '{dst_path}'")
        shutil.move(src=src_path, dst=dst_path)
        os.remove(module)
    except Exception as error:
        print()
        print(f"Compilation {module} failed - '{error}'")
        raise Exception(f"Compilation {module} failed - '{error}'")

def compile_modules_to_pyc():
    print()
    print("Compilation py to pyc started...")
    pool = Pool()
    result_map = pool.map(os.remove, Path(ROOT_DIR).rglob('*.pyc'))
    
    start_time = datetime.now()
    paths = Path(ROOT_DIR).rglob('*.py')
    result_map = pool.map(compile_module_to_pyc, paths)
    process_time = (datetime.now() - start_time).total_seconds()
    print()
    print(f"Compilation of {len(list(result_map))} modules Completed successfully in {process_time:.2f} second.")
    print()

if __name__ == "__main__":
    compile_modules_to_pyc()
