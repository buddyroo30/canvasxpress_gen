NAME=canvasxpress_gen
NAME_DEV=canvasxpress_gen_dev
VERSION:=0.1
REGISTRY=483421617021.dkr.ecr.us-east-1.amazonaws.com
RUN_ARGS= --rm -p 5008:5000
RUN_ARGS_DEV= --rm -p 5009:5000
PROD=-e DEV=False
DEV=-e DEV=True
BIND_MOUNT_ARGS= -v ~/.cache:/root/.cache
GPU_ARGS= --gpus all
SHELL_EXTRA_ARGS=


build: 
	docker build --platform linux/amd64 -t ${REGISTRY}/${NAME}:${VERSION} \
                        -t ${NAME}:${VERSION} \
                        -f Dockerfile .

build_dev: 
	docker build --platform linux/amd64 -t ${REGISTRY}/${NAME_DEV}:${VERSION} \
                        -t ${NAME_DEV}:${VERSION} \
                        -f Dockerfile .

buildfresh: 
	docker build --platform linux/amd64 -t ${REGISTRY}/${NAME}:${VERSION} --no-cache \
                        -t ${NAME}:${VERSION} \
                        -f Dockerfile .

buildfresh_dev: 
	docker build --platform linux/amd64 -t ${REGISTRY}/${NAME_DEV}:${VERSION} --no-cache \
                        -t ${NAME_DEV}:${VERSION} \
                        -f Dockerfile .

run:
	docker run -d ${RUN_ARGS} ${PROD} ${BIND_MOUNT_ARGS} ${NAME}:${VERSION}

run_dev:
	docker run -d ${RUN_ARGS_DEV} ${DEV} ${BIND_MOUNT_ARGS} ${NAME_DEV}:${VERSION}

runi:
	docker run -it ${RUN_ARGS} ${PROD} ${BIND_MOUNT_ARGS} ${NAME}:${VERSION}

runi_dev:
	docker run -it ${RUN_ARGS_DEV} ${DEV} ${BIND_MOUNT_ARGS} ${NAME_DEV}:${VERSION}

shell:
	docker run -it --rm --privileged ${BIND_MOUNT_ARGS} ${PROD} ${NAME}:${VERSION} /bin/bash

shell_dev:
	docker run -it --rm --privileged ${BIND_MOUNT_ARGS} ${DEV} ${NAME_DEV}:${VERSION} /bin/bash

init:
	docker run --rm --privileged ${BIND_MOUNT_ARGS} ${PROD} ${NAME}:${VERSION} /bin/bash -c "python3 vectorize_schema_few_shots.py"

init_dev:
	docker run --rm --privileged ${BIND_MOUNT_ARGS} ${DEV} ${NAME_DEV}:${VERSION} /bin/bash -c "python3 vectorize_schema_few_shots.py"
