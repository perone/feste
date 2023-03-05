from invoke import task


@task
def test(c):
    c.run("python -m pytest --cov=feste tests/")


@task
def all_lint(c):
    lint(c)
    type_check(c)
    isort(c)


@task
def lint(c):
    print("Running flake8...")
    c.run("flake8 --show-source --statistics feste examples")


@task
def type_check(c):
    print("Running mypy...")
    c.run('mypy feste examples')


@task
def isort(c):
    print("Running isort...")
    c.run('isort -c .')


@task
def docstyle(c):
    print("Running pydocstyle...")
    c.run('pydocstyle feste')


@task
def isort_fix(c):
    c.run('isort feste tests docs examples')


@task
def watch_docs(c):
    c.run("sphinx-autobuild docs/source docs/build")


@task
def make_docs(c):
    c.run("cd docs; make html")
