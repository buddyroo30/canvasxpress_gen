NAME=canvasxpress_gen
NAME_DEV=canvasxpress_gen_dev
VERSION:=0.1
RUN_ARGS= --rm -p 5008:5000
RUN_ARGS_DEV= --rm -p 5009:5000
PROD=-e DEV=False
DEV=-e DEV=True
AWS_CREDS_BIND_MOUNT= -v ~/.aws/credentials:/root/.aws/credentials
BIND_MOUNT_ARGS= -v ~/.cache:/root/.cache 
SHELL_EXTRA_ARGS=


build: 
	docker build --platform linux/amd64 \
                        -t ${NAME}:${VERSION} \
                        -f Dockerfile .

build_dev: 
	docker build --platform linux/amd64 \
                        -t ${NAME_DEV}:${VERSION} \
                        -f Dockerfile .

buildfresh: 
	docker build --platform linux/amd64 --no-cache \
                        -t ${NAME}:${VERSION} \
                        -f Dockerfile .

buildfresh_dev: 
	docker build --platform linux/amd64 --no-cache \
                        -t ${NAME_DEV}:${VERSION} \
                        -f Dockerfile .

run:
	docker run -d ${RUN_ARGS} ${PROD} ${BIND_MOUNT_ARGS} ${AWS_CREDS_BIND_MOUNT}--name ${NAME} ${NAME}:${VERSION}

run_dev:
	docker run -d ${RUN_ARGS_DEV} ${DEV} ${BIND_MOUNT_ARGS} ${AWS_CREDS_BIND_MOUNT} --name ${NAME_DEV} ${NAME_DEV}:${VERSION}

runi:
	docker run -it ${RUN_ARGS} ${PROD} ${BIND_MOUNT_ARGS} ${AWS_CREDS_BIND_MOUNT} --name ${NAME} ${NAME}:${VERSION}

runi_dev:
	docker run -it ${RUN_ARGS_DEV} ${DEV} ${BIND_MOUNT_ARGS} ${AWS_CREDS_BIND_MOUNT} --name ${NAME_DEV} ${NAME_DEV}:${VERSION}

exit:
	docker rm -f ${NAME}

exit_dev:
	docker rm -f ${NAME_DEV}

shell:
	docker run -it --rm --privileged ${BIND_MOUNT_ARGS} ${AWS_CREDS_BIND_MOUNT} ${PROD} ${NAME}:${VERSION} /bin/bash

shell_dev:
	docker run -it --rm --privileged ${BIND_MOUNT_ARGS} ${AWS_CREDS_BIND_MOUNT} ${DEV} ${NAME_DEV}:${VERSION} /bin/bash

init:
	docker run --rm --privileged ${BIND_MOUNT_ARGS} ${AWS_CREDS_BIND_MOUNT} ${PROD} ${NAME}:${VERSION} /bin/bash -c "rm -fr /root/.cache/canvasxpress_llm.db; python3 vectorize_schema_few_shots.py"

init_dev:
	docker run --rm --privileged ${BIND_MOUNT_ARGS} ${AWS_CREDS_BIND_MOUNT} ${DEV} ${NAME_DEV}:${VERSION} /bin/bash -c "rm -fr /root/.cache/canvasxpress_llm_dev.db; python3 vectorize_schema_few_shots.py"
