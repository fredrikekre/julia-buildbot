################################################################
# Define everything needed to do per-commit doctesting on Linux
################################################################
import os

# 1. Get a git clone of the correct commit
# 2. Get the built tarball
# 3. Run doctests
# 4. Submit preview docs

# Steps to download a linux tarball, extract it, run doctest on it,
# and, if successful, upload rendered HTML
julia_documentation_factory = util.BuildFactory()
julia_documentation_factory.useProgress = True
julia_documentation_factory.addSteps([
    # Fetch first (allowing failure if no existing clone is present)
    steps.ShellCommand(
        name="git fetch",
        command=["git", "fetch", "--tags", "--all", "--force"],
        flunkOnFailure=False
    ),

    # Clone julia
    # Q: Need to assert that the commit here on the PR is the same as the one we built,
    # alternatively manually check out that commit.
    steps.Git(
        name="Julia checkout",
        repourl=util.Property('repository', default='git://github.com/JuliaLang/julia.git'),
        mode='full',
        method='fresh',
        submodules=True,
        clobberOnFailure=True,
        progress=True,
        retryFetch=True,
        getDescription=True,
    ),

    # Download the appropriate tarball and extract it
    # Q: This will get the one just built for the PR?
    steps.ShellCommand(
        name="Download Julia",
        command=download_julia,
        # julia_exec="bin/julia" # Q: Set as property 'julia_exec' with abspath ??
    ),

    # Run doctests!
    steps.ShellCommand(
        name="Run doctests",
        command=["/bin/sh", "-c", util.Interpolate("%(prop:make_cmd)s -C doc html doctest=true JULIA_EXECUTABLE=%(prop:julia_exec)s")],
        haltOnFailure = True,
        timeout=1000,
    ),

    # TODO: Submit preview docs, could either be the ones from the step above or from the built tarball
])


# Add a dependent scheduler for running coverage after we build tarballs
julia_coverage_builders = ["documentation_linux64"]
# TODO: This should be AnyBranchScheduler similar to package.py
julia_coverage_scheduler = schedulers.Triggerable(name="Julia Coverage Testing", builderNames=julia_coverage_builders)
c['schedulers'].append(julia_coverage_scheduler)

c['schedulers'].append(schedulers.ForceScheduler(
    name="force_coverage",
    label="Force coverage build",
    builderNames=julia_coverage_builders,
    reason=util.FixedParameter(name="reason", default=""),
    codebases=[
        util.CodebaseParameter(
            "",
            name="",
            branch=util.FixedParameter(name="branch", default=""),
            revision=util.FixedParameter(name="revision", default=""),
            repository=util.FixedParameter(name="repository", default=""),
            project=util.FixedParameter(name="project", default="Coverage"),
        )
    ],
    properties=[
        util.StringParameter(
            name="download_url",
            size=60,
            default="https://julialangnightlies-s3.julialang.org/bin/linux/x64/julia-latest-linux64.tar.gz"
        ),
    ]
))

# Add coverage builders
c['builders'].append(util.BuilderConfig(
    name="documentation_linux64",
    workernames=["tabularasa_" + x for x in builder_mapping["linux64"]],
    tags=["Coverage"],
    factory=julia_coverage_factory
))
