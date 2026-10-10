FROM python:3.13-slim-bookworm

# uv installs the exact dependency versions recorded in uv.lock.
COPY --from=ghcr.io/astral-sh/uv:0.11.0 /uv /usr/local/bin/uv
RUN apt-get update \
    && apt-get install -y --no-install-recommends openssh-client tmux rsync ca-certificates \
    && rm -rf /var/lib/apt/lists/*

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    UV_PYTHON_DOWNLOADS=never \
    PATH="/app/.venv/bin:$PATH" \
    HOME=/home/app
WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY main.py README.md ./
COPY core/ ./core/
COPY cli/ ./cli/
COPY ssh/ ./ssh/
COPY utils/ ./utils/
RUN useradd --create-home --uid 1000 app \
    && mkdir -p /home/app/.ssh-cred-manager/keys /home/app/.ssh \
    && chown -R app:app /home/app \
    && chmod 700 /home/app/.ssh-cred-manager /home/app/.ssh-cred-manager/keys /home/app/.ssh
USER app
ENTRYPOINT ["python", "/app/main.py"]
CMD ["connect"]
