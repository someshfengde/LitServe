# Copyright The Lightning AI team.
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
import json
import requests
import subprocess
import time
from openai import OpenAI


def test_e2e_default_api(killall):
    process = subprocess.Popen(
        ["python", "tests/e2e/default_api.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )

    time.sleep(5)
    resp = requests.post("http://127.0.0.1:8000/predict", json={"input": 4.0}, headers=None)
    assert resp.status_code == 200, f"Expected response to be 200 but got {resp.status_code}"
    assert resp.json() == {"output": 16.0}, "tests/simple_server.py didn't return expected output"
    killall(process)


def test_e2e_default_spec(openai_request_data, killall):
    process = subprocess.Popen(
        ["python", "tests/e2e/default_spec.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )

    time.sleep(5)
    resp = requests.post("http://127.0.0.1:8000/v1/chat/completions", json=openai_request_data)
    assert resp.status_code == 200, f"Expected response to be 200 but got {resp.status_code}"
    output = resp.json()["choices"][0]["message"]["content"]
    expected = "This is a generated output"
    assert output == expected, "tests/default_spec.py didn't return expected output"
    killall(process)


def test_e2e_default_batching(killall):
    process = subprocess.Popen(
        ["python", "tests/e2e/default_batching.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )

    time.sleep(5)
    resp = requests.post("http://127.0.0.1:8000/predict", json={"input": 4.0}, headers=None)
    assert resp.status_code == 200, f"Expected response to be 200 but got {resp.status_code}"
    assert resp.json() == {"output": 16.0}, "tests/simple_server.py didn't return expected output"
    killall(process)


def test_e2e_batched_streaming(killall):
    process = subprocess.Popen(
        ["python", "tests/e2e/default_batched_streaming.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )

    time.sleep(5)
    resp = requests.post("http://127.0.0.1:8000/predict", json={"input": 4.0}, headers=None, stream=True)
    assert resp.status_code == 200, f"Expected response to be 200 but got {resp.status_code}"

    outputs = []
    for line in resp.iter_content(chunk_size=4000):
        if line:
            outputs.append(json.loads(line.decode("utf-8")))

    assert len(outputs) == 10, "streaming server should have 10 outputs"
    assert {"output": 16.0} in outputs, "server didn't return expected output"
    killall(process)


def test_openai_parity(killall):
    process = subprocess.Popen(
        ["python", "tests/e2e/default_openaispec.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )
    time.sleep(5)
    client = OpenAI(
        base_url="http://127.0.0.1:8000/v1",
        api_key="lit",  # required, but unused
    )
    response = client.chat.completions.create(
        model="lit",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "How are you?"},
        ],
    )
    assert response.choices[0].message.content == "This is a generated output", (
        f"Server didn't return expected output" f"\nOpenAI client output: {response}"
    )

    response = client.chat.completions.create(
        model="lit",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "How are you?"},
        ],
        stream=True,
    )

    expected_outputs = ["This is a generated output", None]
    for r, expected_out in zip(response, expected_outputs):
        assert r.choices[0].delta.content == expected_out, (
            f"Server didn't return expected output.\n" f"OpenAI client output: {r}"
        )

    killall(process)


def test_openai_parity_with_image_input(killall):
    process = subprocess.Popen(
        ["python", "tests/e2e/default_openaispec.py"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        stdin=subprocess.DEVNULL,
    )
    time.sleep(5)
    client = OpenAI(
        base_url="http://127.0.0.1:8000/v1",
        api_key="lit",  # required, but unused
    )
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "What's in this image?"},
                {
                    "type": "image_url",
                    "image_url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                },
            ],
        },
    ]
    response = client.chat.completions.create(
        model="lit",
        messages=messages,
    )
    assert response.choices[0].message.content == "This is a generated output", (
        f"Server didn't return expected output" f"\nOpenAI client output: {response}"
    )

    response = client.chat.completions.create(
        model="lit",
        messages=messages,
        stream=True,
    )

    expected_outputs = ["This is a generated output", None]
    for r, expected_out in zip(response, expected_outputs):
        assert r.choices[0].delta.content == expected_out, (
            f"Server didn't return expected output.\n" f"OpenAI client output: {r}"
        )

    killall(process)
