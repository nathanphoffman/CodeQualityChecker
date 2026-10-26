from pathlib import Path

import pytest

from codequality import report
from codequality.detect import detect
from codequality.registry import all_rules

def grade(root: Path, rule_id: str):
    return {rule.id: result for rule, result in report.run(detect(root), all_rules())}[rule_id]

def write_files(root: Path, files: dict) -> Path:
    for name, text in files.items():
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_text(text)

    return root

# rule id -> (project files that should trip it, project files that should pass it)
FRAMEWORK_CASES = {
    "PYTHON-DJANGO-001": ({"requirements.txt": "Django>=4\n", "settings.py": "ALLOWED_HOSTS = ['*']\n"}, {"requirements.txt": "Django>=4\n", "settings.py": "ALLOWED_HOSTS = ['a.com']\n"}),
    "PYTHON-DJANGO-002": ({"requirements.txt": "django\n", "settings.py": "DEBUG = True\n"}, {"requirements.txt": "django\n", "settings.py": "DEBUG = False\n"}),
    "PYTHON-DJANGO-003": ({"requirements.txt": "django\n", "views.py": "@csrf_exempt\ndef view(request):\n    pass\n"}, {"requirements.txt": "django\n", "views.py": "def view(request):\n    pass\n"}),
    "PYTHON-FLASK-001": ({"requirements.txt": "flask\n", "app.py": "def page(text):\n    return render_template_string(text)\n"}, {"requirements.txt": "flask\n", "app.py": "def page():\n    return render_template_string('hi')\n"}),
    "PYTHON-FASTAPI-001": ({"requirements.txt": "fastapi\n", "api.py": "@app.get('/a')\ndef read(db=Depends(get_db)):\n    return 1\n"}, {"requirements.txt": "fastapi\n", "api.py": "@app.get('/a')\ndef read(db=Depends(get_db)) -> int:\n    return 1\n"}),
    "PYTHON-FASTAPI-002": ({"requirements.txt": "fastapi\n", "api.py": "async def read():\n    time.sleep(1)\n"}, {"requirements.txt": "fastapi\n", "api.py": "async def read():\n    await asyncio.sleep(1)\n"}),
    "RUST-AXUM-001": ({"Cargo.toml": "[dependencies]\naxum = '0.7'\n", "main.rs": "fn f() { DefaultBodyLimit::disable(); }\n"}, {"Cargo.toml": "[dependencies]\naxum = '0.7'\n", "main.rs": "fn f() {}\n"}),
    "RUST-AXUM-002": ({"Cargo.toml": "[dependencies]\naxum = '0.7'\n", "main.rs": "async fn f() { std::thread::sleep(d); }\n"}, {"Cargo.toml": "[dependencies]\naxum = '0.7'\n", "main.rs": "async fn f() { tokio::time::sleep(d).await; }\n"}),
    "RUST-ACTIX-001": ({"Cargo.toml": "[dependencies]\nactix-web = '4'\n", "main.rs": "async fn f() { std::fs::read(p); }\n"}, {"Cargo.toml": "[dependencies]\nactix-web = '4'\n", "main.rs": "async fn f() { tokio::fs::read(p).await; }\n"}),
    "RUST-TAURI-001": ({"Cargo.toml": "[dependencies]\ntauri = '1'\n", "tauri.conf.json": '{"security": {"csp": null}}'}, {"Cargo.toml": "[dependencies]\ntauri = '1'\n", "tauri.conf.json": '{"security": {"csp": "default-src self"}}'}),
    "RUST-TAURI-002": ({"Cargo.toml": "[dependencies]\ntauri = '1'\n", "tauri.conf.json": '{"allowlist": {"all": true}}'}, {"Cargo.toml": "[dependencies]\ntauri = '1'\n", "tauri.conf.json": '{"allowlist": {"all": false}}'}),
    "TS-REACT-001": ({"package.json": '{"dependencies": {"react": "18"}}', "list.tsx": "const a = items.map((item, i) => <li key={i} />);\n"}, {"package.json": '{"dependencies": {"react": "18"}}', "list.tsx": "const a = items.map((item) => <li key={item.id} />);\n"}),
    "TS-REACT-002": ({"package.json": '{"dependencies": {"react": "18"}}', "a.tsx": "const a = document.getElementById('x');\n"}, {"package.json": '{"dependencies": {"react": "18"}}', "a.tsx": "const a = ref.current;\n"}),
    "TS-EXPRESS-001": ({"package.json": '{"dependencies": {"express": "4"}}', "app.ts": "const app = express();\n"}, {"package.json": '{"dependencies": {"express": "4"}}', "app.ts": "app.use(helmet());\n"}),
    "TS-EXPRESS-002": ({"package.json": '{"dependencies": {"express": "4"}}', "app.ts": "const app = express();\n"}, {"package.json": '{"dependencies": {"express": "4"}}', "app.ts": "app.use((err: Error, req: Request, res: Response, next: NextFunction) => next());\n"}),
    "TS-NEST-001": ({"package.json": '{"dependencies": {"@nestjs/core": "10"}}', "main.ts": "const app = 1;\n"}, {"package.json": '{"dependencies": {"@nestjs/core": "10"}}', "main.ts": "app.useGlobalPipes(new ValidationPipe());\n"}),
    "TS-NEST-002": ({"package.json": '{"dependencies": {"@nestjs/core": "10"}}', "c.ts": "class C { create(@Body() body: any) {} }\n"}, {"package.json": '{"dependencies": {"@nestjs/core": "10"}}', "c.ts": "class C { create(@Body() body: CreateDto) {} }\n"}),
    "TS-VUE-001": ({"package.json": '{"dependencies": {"vue": "3"}}', "A.vue": '<template><div v-html="x"></div></template>\n'}, {"package.json": '{"dependencies": {"vue": "3"}}', "A.vue": '<template><div>{{ x }}</div></template>\n'}),
    "TS-VUE-002": ({"package.json": '{"dependencies": {"vue": "3"}}', "A.vue": '<template><li v-for="i in items">{{ i }}</li></template>\n'}, {"package.json": '{"dependencies": {"vue": "3"}}', "A.vue": '<template><li v-for="i in items" :key="i.id">{{ i }}</li></template>\n'}),
    "TS-ANGULAR-001": ({"package.json": '{"dependencies": {"@angular/core": "17"}}', "a.ts": "const x = sanitizer.bypassSecurityTrustHtml(text);\n"}, {"package.json": '{"dependencies": {"@angular/core": "17"}}', "a.ts": "const x = text;\n"}),
    "TS-ANGULAR-002": ({"package.json": '{"dependencies": {"@angular/core": "17"}}', "a.ts": "@Component({selector: 'a'})\nclass A {}\n"}, {"package.json": '{"dependencies": {"@angular/core": "17"}}', "a.ts": "@Component({changeDetection: ChangeDetectionStrategy.OnPush})\nclass A {}\n"}),
    "RUST-ROCKET-001": ({"Cargo.toml": "[dependencies]\nrocket = '0.5'\n", "main.rs": "async fn f() { std::thread::sleep(d); }\n"}, {"Cargo.toml": "[dependencies]\nrocket = '0.5'\n", "main.rs": "async fn f() { tokio::time::sleep(d).await; }\n"}),
    "RUST-ROCKET-002": ({"Cargo.toml": "[dependencies]\nrocket = '0.5'\n", "main.rs": "fn f(body: Json<Value>) {}\n"}, {"Cargo.toml": "[dependencies]\nrocket = '0.5'\n", "main.rs": "fn f(body: Json<Order>) {}\n"}),
    "PYTHON-SQLALCHEMY-001": ({**{"requirements.txt": "sqlalchemy\n"}, **{"db.py": "def f(n):\n    return text(f\"SELECT * FROM u WHERE n = {n}\")\n"}}, {**{"requirements.txt": "sqlalchemy\n"}, **{"db.py": "def f():\n    return text(\"SELECT * FROM u WHERE n = :n\")\n"}}),
    "PYTHON-SQLALCHEMY-002": ({**{"requirements.txt": "sqlalchemy\n"}, **{"db.py": "rows = session.query(User).all()\n"}}, {**{"requirements.txt": "sqlalchemy\n"}, **{"db.py": "rows = session.scalars(select(User))\n"}}),
    "PYTHON-PYDANTIC-001": ({**{"requirements.txt": "pydantic\n"}, **{"m.py": "x = Model.parse_obj(data)\n"}}, {**{"requirements.txt": "pydantic\n"}, **{"m.py": "x = Model.model_validate(data)\n"}}),
    "PYTHON-PYDANTIC-002": ({**{"requirements.txt": "pydantic\n"}, **{"m.py": "class M(BaseModel):\n    model_config = ConfigDict(extra=\"allow\")\n"}}, {**{"requirements.txt": "pydantic\n"}, **{"m.py": "class M(BaseModel):\n    model_config = ConfigDict(extra=\"forbid\")\n"}}),
    "TS-SVELTE-001": ({**{"package.json": '{"dependencies": {"svelte": "4"}}'}, **{"A.svelte": "<div>{@html text}</div>\n"}}, {**{"package.json": '{"dependencies": {"svelte": "4"}}'}, **{"A.svelte": "<div>{text}</div>\n"}}),
    "TS-SVELTE-002": ({**{"package.json": '{"dependencies": {"svelte": "4"}}'}, **{"A.svelte": "{#each items as item}<li>{item}</li>{/each}\n"}}, {**{"package.json": '{"dependencies": {"svelte": "4"}}'}, **{"A.svelte": "{#each items as item (item.id)}<li>{item}</li>{/each}\n"}}),
    "TS-NUXT-001": ({**{"package.json": '{"dependencies": {"nuxt": "3"}}'}, **{"nuxt.config.ts": "export default { runtimeConfig: { public: { apiToken: 1 } } }\n"}}, {**{"package.json": '{"dependencies": {"nuxt": "3"}}'}, **{"nuxt.config.ts": "export default { runtimeConfig: { public: { siteName: 1 } } }\n"}}),
    "TS-NUXT-002": ({**{"package.json": '{"dependencies": {"nuxt": "3"}}'}, **{"server/a.ts": "const body = await readBody(event);\n"}}, {**{"package.json": '{"dependencies": {"nuxt": "3"}}'}, **{"server/a.ts": "const body = await readValidatedBody(event, check);\n"}}),
    "TS-FASTIFY-001": ({**{"package.json": '{"dependencies": {"fastify": "4"}}'}, **{"app.ts": "app.get(\"/a\", { }, handler);\n"}}, {**{"package.json": '{"dependencies": {"fastify": "4"}}'}, **{"app.ts": "app.get(\"/a\", { schema: s }, handler);\n"}}),
    "TS-FASTIFY-002": ({**{"package.json": '{"dependencies": {"fastify": "4"}}'}, **{"app.ts": "const app = fastify();\n"}}, {**{"package.json": '{"dependencies": {"fastify": "4"}}'}, **{"app.ts": "const app = fastify({ logger: true });\n"}}),
    "RUST-DIESEL-001": ({**{"Cargo.toml": "[dependencies]\ndiesel = '2'\n"}, **{"main.rs": "fn f() { sql_query(format!(\"SELECT {}\", x)); }\n"}}, {**{"Cargo.toml": "[dependencies]\ndiesel = '2'\n"}, **{"main.rs": "fn f() { sql_query(\"SELECT 1\"); }\n"}}),
    "RUST-SQLX-001": ({**{"Cargo.toml": "[dependencies]\nsqlx = '0.7'\n"}, **{"main.rs": "fn f() { sqlx::query(&format!(\"SELECT {}\", x)); }\n"}}, {**{"Cargo.toml": "[dependencies]\nsqlx = '0.7'\n"}, **{"main.rs": "fn f() { sqlx::query(\"SELECT 1\"); }\n"}}),
    "RUST-BEVY-001": ({**{"Cargo.toml": "[dependencies]\nbevy = '0.13'\n"}, **{"main.rs": "fn f() { std::thread::sleep(d); }\n"}}, {**{"Cargo.toml": "[dependencies]\nbevy = '0.13'\n"}, **{"main.rs": "fn f() {}\n"}}),
    "GO-NETHTTP-001": ({**{"go.mod": "module a\n"}, **{"main.go": "package main\nimport \"net/http\"\nfunc main() { http.ListenAndServe(\":80\", nil) }\n"}}, {**{"go.mod": "module a\n"}, **{"main.go": "package main\nimport \"net/http\"\nfunc main() { s.ListenAndServe() }\n"}}),
    "GO-NETHTTP-002": ({**{"go.mod": "module a\n"}, **{"main.go": "package main\nimport \"net/http\"\nfunc main() { http.Get(u) }\n"}}, {**{"go.mod": "module a\n"}, **{"main.go": "package main\nimport \"net/http\"\nfunc main() { c.Get(u) }\n"}}),
    "GO-GORM-001": ({**{"go.mod": "require gorm.io/gorm v1\n"}, **{"main.go": "package main\nfunc f() { db.Raw(fmt.Sprintf(\"SELECT %s\", x)) }\n"}}, {**{"go.mod": "require gorm.io/gorm v1\n"}, **{"main.go": "package main\nfunc f() { db.Raw(\"SELECT ?\", x) }\n"}}),
    "CSHARP-UNITY-001": ({**{"ProjectSettings/ProjectVersion.txt": "2022"}, **{"P.cs": "class P { void Update() { var g = GameObject.Find(\"x\"); } }\n"}}, {**{"ProjectSettings/ProjectVersion.txt": "2022"}, **{"P.cs": "class P { void Start() { var g = GameObject.Find(\"x\"); } void Update() { } }\n"}}),
    "CSHARP-UNITY-002": ({**{"ProjectSettings/ProjectVersion.txt": "2022"}, **{"P.cs": "class P { void Start() { Debug.Log(1); } }\n"}}, {**{"ProjectSettings/ProjectVersion.txt": "2022"}, **{"P.cs": "class P { void Start() { } }\n"}}),
    "GO-GIN-001": ({"go.mod": "require github.com/gin-gonic/gin v1.9\n", "main.go": "package main\n"}, {"go.mod": "require github.com/gin-gonic/gin v1.9\n", "main.go": "package main\nfunc init() { gin.SetMode(gin.ReleaseMode) }\n"}),
    "GO-GIN-002": ({"go.mod": "require github.com/gin-gonic/gin v1.9\n", "main.go": "package main\n"}, {"go.mod": "require github.com/gin-gonic/gin v1.9\n", "main.go": "package main\nfunc init() { r.SetTrustedProxies(nil) }\n"}),
    "GO-ECHO-001": ({"go.mod": "require github.com/labstack/echo/v4 v4\n", "main.go": "package main\n"}, {"go.mod": "require github.com/labstack/echo/v4 v4\n", "main.go": "package main\nfunc init() { e.Use(middleware.Recover()) }\n"}),
    "GO-ECHO-002": ({"go.mod": "require github.com/labstack/echo/v4 v4\n", "main.go": "package main\nfunc init() { e.Debug = true }\n"}, {"go.mod": "require github.com/labstack/echo/v4 v4\n", "main.go": "package main\n"}),
    "GO-FIBER-001": ({"go.mod": "require github.com/gofiber/fiber/v2 v2\n", "main.go": "package main\n"}, {"go.mod": "require github.com/gofiber/fiber/v2 v2\n", "main.go": "package main\nfunc init() { app.Use(recover.New()) }\n"}),
    "CSHARP-ASPNET-001": ({"a.csproj": '<Project Sdk="Microsoft.NET.Sdk.Web"/>', "Program.cs": "class P {}\n"}, {"a.csproj": '<Project Sdk="Microsoft.NET.Sdk.Web"/>', "Program.cs": "class P { void M() { app.UseHttpsRedirection(); } }\n"}),
    "CSHARP-ASPNET-002": ({"a.csproj": '<Project Sdk="Microsoft.NET.Sdk.Web"/>', "Program.cs": "class P {}\n"}, {"a.csproj": '<Project Sdk="Microsoft.NET.Sdk.Web"/>', "Program.cs": "class P { void M() { app.UseHsts(); } }\n"}),
    "CSHARP-ASPNET-003": ({"a.csproj": '<Project Sdk="Microsoft.NET.Sdk.Web"/>', "Program.cs": "class P { void M() { var x = task.Result; } }\n"}, {"a.csproj": '<Project Sdk="Microsoft.NET.Sdk.Web"/>', "Program.cs": "class P { void M() { var x = await task; } }\n"}),
    "CSHARP-EFCORE-001": ({"a.csproj": "<PackageReference Include=\"Microsoft.EntityFrameworkCore\"/>", "Db.cs": 'class D { void M() { db.Users.FromSqlRaw($"SELECT * FROM U WHERE N = {name}"); } }\n'}, {"a.csproj": "<PackageReference Include=\"Microsoft.EntityFrameworkCore\"/>", "Db.cs": 'class D { void M() { db.Users.FromSqlRaw("SELECT * FROM U WHERE N = {0}", name); } }\n'}),
    "CSHARP-BLAZOR-001": ({"a.csproj": '<Project Sdk="Microsoft.NET.Sdk.BlazorWebAssembly"/>', "Page.razor": "@code { void M() { task.Wait(); } }\n"}, {"a.csproj": '<Project Sdk="Microsoft.NET.Sdk.BlazorWebAssembly"/>', "Page.razor": "@code { async Task M() { await task; } }\n"}),
}

@pytest.mark.parametrize("rule_id", sorted(FRAMEWORK_CASES))
def test_framework_check_flags_the_bad_project_and_passes_the_good_one(tmp_path: Path, rule_id: str):
    bad, good = FRAMEWORK_CASES[rule_id]
    bad_root, good_root = tmp_path / "bad", tmp_path / "good"
    bad_root.mkdir()
    good_root.mkdir()

    assert grade(write_files(bad_root, bad), rule_id).score < 1.0
    assert grade(write_files(good_root, good), rule_id).score == 1.0

def test_a_framework_rule_only_runs_when_the_project_uses_it(tmp_path: Path):
    write_files(tmp_path, {"requirements.txt": "flask-cors\n", "app.py": "x = 1\n"})

    assert "PYTHON-FLASK-001" not in {rule.id for rule in all_rules() if rule.applies_to(detect(tmp_path))}

# language -> (files that have no formatter or linter set up, files that do)
TOOLING_CASES = {
    "PYTHON-001": ({"a.py": "x = 1\n"}, {"a.py": "x = 1\n", "pyproject.toml": "[tool.ruff]\nline-length = 100\n"}),
    "GO-001": ({"go.mod": "module a\n"}, {"go.mod": "module a\n", ".golangci.yml": "run: {}\n"}),
    "C-001": ({"a.c": "int x;\n"}, {"a.c": "int x;\n", ".clang-format": "", ".clang-tidy": ""}),
    "CSHARP-001": ({"a.cs": "class A {}\n"}, {"a.cs": "class A {}\n", ".editorconfig": "root = true\n"}),
    "FORTRAN-001": ({"a.f90": "program a\nend program a\n"}, {"a.f90": "program a\nend program a\n", ".fprettify.rc": ""}),
}

@pytest.mark.parametrize("rule_id", sorted(TOOLING_CASES))
def test_format_and_lint_config_is_required(tmp_path: Path, rule_id: str):
    missing, present = TOOLING_CASES[rule_id]
    missing_root, present_root = tmp_path / "missing", tmp_path / "present"
    missing_root.mkdir()
    present_root.mkdir()

    assert grade(write_files(missing_root, missing), rule_id).score == 0.0
    assert grade(write_files(present_root, present), rule_id).score == 1.0

def test_pyproject_without_a_tool_section_does_not_count(tmp_path: Path):
    write_files(tmp_path, {"a.py": "x = 1\n", "pyproject.toml": "[project]\nname = 'a'\n"})

    assert grade(tmp_path, "PYTHON-001").score == 0.0
