FROM ghcr.io/astral-sh/uv:0.11.24@sha256:99ea34acedc870ba4ad11a1f540a1c04267c9f30aadc465a94406f52dfda2c36 AS uv

FROM python:3.12-slim-bookworm@sha256:0f5b26b9518d002b6173fd61daad821fa340635ebfec5bba471013f9ca114579

RUN apt-get update \
    && apt-get install --yes --no-install-recommends \
        build-essential \
        ca-certificates \
        curl \
        xz-utils \
        zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

COPY --from=uv /uv /uvx /usr/local/bin/
COPY ci/toolchains/git-2.39.5.sha256 /tmp/git-build/git-2.39.5.sha256

WORKDIR /tmp/git-build
RUN curl --fail --location --remote-name \
        https://www.kernel.org/pub/software/scm/git/git-2.39.5.tar.xz \
    && sha256sum --check git-2.39.5.sha256 \
    && tar --extract --file git-2.39.5.tar.xz \
    && make --directory git-2.39.5 --jobs 2 \
        prefix=/usr/local \
        NO_CURL=YesPlease \
        NO_EXPAT=YesPlease \
        NO_GETTEXT=YesPlease \
        NO_OPENSSL=YesPlease \
        NO_PERL=YesPlease \
        NO_PYTHON=YesPlease \
        NO_TCLTK=YesPlease \
    && make --directory git-2.39.5 \
        prefix=/usr/local \
        NO_CURL=YesPlease \
        NO_EXPAT=YesPlease \
        NO_GETTEXT=YesPlease \
        NO_OPENSSL=YesPlease \
        NO_PERL=YesPlease \
        NO_PYTHON=YesPlease \
        NO_TCLTK=YesPlease \
        install \
    && test "$(git --version)" = "git version 2.39.5" \
    && rm -rf /tmp/git-build

WORKDIR /workspace
