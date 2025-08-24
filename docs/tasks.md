Skip to content
Navigation Menu
KAFKA2306
magicaltexture

Type / to search
Code
Issues
Pull requests
Actions
Projects
Wiki
Security
Insights
Settings
CI & Deploy to HuggingFace Spaces
first commit #11
Jobs
Run details
Annotations
1 error
Deploy to HuggingFace Spaces
failed 1 minute ago in 9s
Search logs
1s
1s
0s
5s
0s
1s
The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "/opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages/huggingface_hub/hf_api.py", line 9710, in _validate_yaml
    hf_raise_for_status(response)
  File "/opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages/huggingface_hub/utils/_http.py", line 465, in hf_raise_for_status
    raise _format(BadRequestError, message, response) from e
huggingface_hub.errors.BadRequestError: (Request ID: Root=1-68aaf032-5f421f174fbdbf39345ef35d;fb96010a-d4f1-410b-b79a-2f95d50d77eb)

Bad request:
"colorFrom" must be one of [red, yellow, green, blue, indigo, purple, pink, gray]

The above exception was the direct cause of the following exception:

Traceback (most recent call last):
  File "<stdin>", line 9, in <module>
  File "/opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages/huggingface_hub/utils/_validators.py", line 114, in _inner_fn
    return fn(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages/huggingface_hub/hf_api.py", line 1669, in _inner
    return fn(self, *args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages/huggingface_hub/hf_api.py", line 4963, in upload_folder
    add_operations = self._prepare_upload_folder_additions(
                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages/huggingface_hub/hf_api.py", line 9649, in _prepare_upload_folder_additions
    self._validate_yaml(
  File "/opt/hostedtoolcache/Python/3.11.13/x64/lib/python3.11/site-packages/huggingface_hub/hf_api.py", line 9714, in _validate_yaml
    raise ValueError(f"Invalid metadata in README.md.\n{message}") from e
ValueError: Invalid metadata in README.md.
- "colorFrom" must be one of [red, yellow, green, blue, indigo, purple, pink, gray]
Error: Process completed with exit code 1.
0s
0s
0s
0s
