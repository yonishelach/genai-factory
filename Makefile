# Copyright 2023 Iguazio
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

CONTROLLER_NAME = genai-factory-controller

.PHONY: controller
controller:
	# Build controller's image:
	docker build -f controller/Dockerfile -t $(CONTROLLER_NAME):latest .

	# Run controller locally in a container:
	docker run -d --net host --name $(CONTROLLER_NAME) $(CONTROLLER_NAME):latest

	# Announce the server is running:
	@echo "GenAI Factory Controller is running in the background"
