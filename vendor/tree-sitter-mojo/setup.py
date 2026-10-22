from setuptools import Extension, setup

setup(ext_modules=[Extension(
    name="tree_sitter_mojo._binding",
    sources=["tree_sitter_mojo/binding.c", "src/parser.c", "src/scanner.c"],
    include_dirs=["src"],
    extra_compile_args=["-std=c11"],
)])
