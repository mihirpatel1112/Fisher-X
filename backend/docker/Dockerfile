# docker/Dockerfile
FROM mambaorg/micromamba:1.5.8

USER root
RUN apt-get update && apt-get install -y git curl build-essential && rm -rf /var/lib/apt/lists/*

# 工作目录要和你的项目文件夹名一致（你的是 nasa-clean-skies）
WORKDIR /workspaces/nasa-clean-skies

# 预装依赖（使用你已写好的 environment.yml）
COPY environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && micromamba clean -a -y

ENV PYTHONUNBUFFERED=1
