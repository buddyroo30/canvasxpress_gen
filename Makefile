NAME=canvasxpress_gen
VERSION:=0.1
REGISTRY=483421617021.dkr.ecr.us-east-1.amazonaws.com
RUN_ARGS= --rm -p 5008:5000
BIND_MOUNT_ARGS= -v ~/.cache:/root/.cache
GPU_ARGS= --gpus all
SHELL_EXTRA_ARGS=


build: 
	docker build --platform linux/amd64 -t ${REGISTRY}/${NAME}:${VERSION} \
                        -t ${NAME}:${VERSION} \
                        -f Dockerfile .

buildfresh: 
	docker build --platform linux/amd64 -t ${REGISTRY}/${NAME}:${VERSION} --no-cache \
                        -t ${NAME}:${VERSION} \
                        -f Dockerfile .

buildgpu: 
	docker build --platform linux/amd64 -t ${REGISTRY}/${NAME}:${VERSION}-GPU \
                        -t ${NAME}:${VERSION}-GPU \
                        -f Dockerfile-GPU .

buildfreshgpu: 
	docker build --platform linux/amd64 -t ${REGISTRY}/${NAME}:${VERSION}-GPU --no-cache \
                        -t ${NAME}:${VERSION}-GPU \
                        -f Dockerfile-GPU .

run:
	docker run -d ${RUN_ARGS} ${BIND_MOUNT_ARGS} ${NAME}:${VERSION}

runi:
	docker run -it ${RUN_ARGS} ${BIND_MOUNT_ARGS} ${NAME}:${VERSION}

rungpu:
	docker run -d ${RUN_ARGS} ${GPU_ARGS} ${BIND_MOUNT_ARGS} ${NAME}:${VERSION}-GPU

runigpu:
	docker run -it ${RUN_ARGS} ${GPU_ARGS} ${BIND_MOUNT_ARGS} ${NAME}:${VERSION}-GPU

shell:
	docker run -it --rm --privileged ${BIND_MOUNT_ARGS} ${NAME}:${VERSION} /bin/bash

init:
	docker run --rm --privileged ${BIND_MOUNT_ARGS} ${NAME}:${VERSION} /bin/bash -c "cp /app/schema.txt /root/.cache/schema.txt && cd /app/english_to_config/ && python3 vectorize_schema_few_shots.py"

shellgpu:
	docker run -it ${RUN_ARGS} ${GPU_ARGS} ${SHELL_EXTRA_ARGS} ${BIND_MOUNT_ARGS} --entrypoint /bin/bash ${NAME}:${VERSION}-GPU
