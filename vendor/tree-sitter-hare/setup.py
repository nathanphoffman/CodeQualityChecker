from setuptools import Extension, setup

setup(ext_modules=[Extension(
    name="tree_sitter_hare._binding",
    sources=["tree_sitter_hare/binding.c", "src/parser.c"],
    include_dirs=["src"],
    extra_compile_args=["-std=c11"],
)])
