import torch
import tqdm
import json
import gc
from transformers import AutoModelForCausalLM, AutoTokenizer


class Tools:
    @staticmethod
    def load_jsonl(path):
        with open(path, 'r') as f:
            return [json.loads(line) for line in f.readlines()]
    
    @staticmethod
    def dump_jsonl(obj, path):
        with open(path, 'w') as f:
            for line in obj:
                f.write(json.dumps(line) + '\n')


class QwenInference:
    def __init__(self, model_name="Qwen/Qwen2.5-Coder-0.5B"):
        """
        Initialize the Qwen model for inference with individual record processing.
        
        Args:
            model_name (str): The model name or path
        """
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.model_name = model_name
        
        # Initialize tokenizer
        self.tokenizer = AutoTokenizer.from_pretrained(
            model_name,
        )
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
            
        # Initialize model
        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            device_map="auto"
        ).eval()
        print(f'Model loaded on device: {self.model.device}')
        
    def _clear_cuda_cache(self):
        """Clear CUDA cache to free up memory."""
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            gc.collect()

    def _generate_single(self, prompt, max_new_tokens=10, temperature=0.0, top_p=0.2):
        """Generate completion for a single prompt."""
        print('Processing prompt:', prompt[:50] + '...' if len(prompt) > 50 else prompt)
        
        try:
            # Clear cache before processing
            self._clear_cuda_cache()
            
            # Tokenize
            inputs = self.tokenizer(
                [prompt],
                return_tensors="pt",
            )
            
            # Move inputs to the same device as model
            input_ids = inputs["input_ids"].to(self.model.device)
            attention_mask = inputs["attention_mask"].to(self.model.device)
            
            # Generate
            with torch.no_grad():
                outputs = self.model.generate(
                    input_ids=input_ids,
                    max_new_tokens=max_new_tokens,
                    do_sample=False,
                )[0]
            
            # Decode and remove prompt from response
            gen_text = self.tokenizer.decode(outputs[len(inputs.input_ids[0]):], skip_special_tokens=True)

            # Clear intermediate tensors
            del inputs, input_ids, attention_mask, outputs
            self._clear_cuda_cache()
            
            return gen_text
            
        except RuntimeError as e:
            if "out of memory" in str(e):
                self._clear_cuda_cache()
                raise RuntimeError("Out of memory error when processing. Try reducing max_new_tokens.")
            else:
                raise e

    def process_file(self, file_path, max_new_tokens=100, temperature=0.0, top_p=0.2):
        """Generate completions for all prompts in a JSONL file, processing one record at a time."""
        print(f'Generating from {file_path}')
        print(f'Model device: {self.model.device}')
        print(f'Max new tokens: {max_new_tokens}')
        
        # Load data
        lines = Tools.load_jsonl(file_path)
        new_lines = []
        
        # Process each record individually
        for i, line in enumerate(tqdm.tqdm(lines)):
            prompt = f"{line['prompt']}\n"
            try:
                generated_text = self._generate_single(
                    prompt, 
                    max_new_tokens=max_new_tokens,
                    temperature=temperature,
                    top_p=top_p
                )
                
                new_lines.append({
                    'prompt': line['prompt'],
                    'metadata': line.get('metadata', {}),
                    'choices': [{'text': generated_text}]
                })
                
                # Log progress periodically
                if (i + 1) % 10 == 0:
                    print(f'Processed {i + 1}/{len(lines)} records')
                    
            except Exception as e:
                print(f"Error processing record {i}: {str(e)}")
                # Add empty result to maintain order
                new_lines.append({
                    'prompt': line['prompt'],
                    'metadata': line.get('metadata', {}),
                    'choices': [{'text': "ERROR: " + str(e)}]
                })
        
        print(f'Generated {len(new_lines)} samples')
        
        # Save results
        output_path = file_path.replace('.jsonl', f'_{self.model_name.split("/")[-1]}.jsonl')
        Tools.dump_jsonl(new_lines, output_path)
        return output_path


def main():
    file_path = '/root/evaluation_autocompletion/CodeT/myCode/test_data/repocoder_response_full_batch0.jsonl'

    print('file_path', file_path)

    qwen = QwenInference()
    qwen.process_file(file_path)


if __name__ == "__main__":
    main()
    # from transformers import AutoTokenizer, AutoModelForCausalLM
    # # load model
    # device = "cuda" # the device to load the model onto

    # TOKENIZER = AutoTokenizer.from_pretrained("Qwen/Qwen2.5-Coder-0.5B")
    # MODEL = AutoModelForCausalLM.from_pretrained("Qwen/Qwen2.5-Coder-0.5B", device_map="auto").eval()

    # input_text = "#<|file_sep|>/root/evaluation_autocompletion/DraCo/ReccEval/Source_Code//a13e/a13e-0.0.1/a13e/plugin.py\nimport importlib\nimport pkgutil\nfrom types import ModuleType\nfrom typing import Type, TYPE_CHECKING, Optional, Dict, List\n\n# from a13e import plugins\n\nif TYPE_CHECKING:\n    from a13e.recognizer import BaseRecognizer\n\n\nclass PluginRegister:\n    \"\"\"Plugin Registrar.\n\n    It is used to extend more recognizers, and automatically imports all plugins in the plugins\n    directory of the package path when instantiated. The class attribute dictionary named recognizers is used to\n    store the recognizer, the key is the name of the recognizer, and the value is the instance of the recognizer.\n    \"\"\"\n    recognizers: Dict[str, 'BaseRecognizer'] = {}\n\n    def __init__(self, pkg: ModuleType):\n        self.load_plugins(pkg)\n\n    @classmethod\n    def register(cls, recognizer: Type['BaseRecognizer']):\n        \"\"\"Register and instantiate a recognizer.\"\"\"\n        instance = recognizer()\n        cls.recognizers[instance.name] = instance\n        return instance\n\n    @staticmethod\n    def load_plugins(pkg: ModuleType):\n        plugins: List[ModuleType] = []\n        for module_finder, name, ispkg in pkgutil.iter_modules([pkg.__path__[0]]):\n            if not (module_spec := module_finder.find_spec(name, None)):\n                continue\n            if not module_spec.origin:\n                continue\n\n            module_name = f\"{pkg.__name__}.{name}\"\n            module = importlib.import_module(module_name)\n            if ispkg:\n                PluginRegister.load_plugins(module)\n                continue\n            if module in plugins:\n                continue\n            plugins.append(module)\n\n        return plugins\n\n#<|file_sep|>/root/evaluation_autocompletion/DraCo/ReccEval/Source_Code//a13e/a13e-0.0.1/a13e/plugins/neteasecloudmusic/neteasemusic.py\nclass NeteaseCloudMusic(BaseRecognizer):\n    def recognize(self, audio_fp: Path, **kwargs) -> List[RecognizeResult]:\n        header = {\n            'authority': 'interface.music.163.com',\n            'accept': '*/*',\n            'accept-language': 'en-US,en;q=0.9,zh-CN;q=0.8,zh;q=0.7',\n            'cache-control': 'max-age=0',\n            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',\n            'origin': 'chrome-extension://pgphbbekcgpfaekhcbjamjjkegcclhhd',\n            'sec-ch-ua': '\" Not A;Brand\";v=\"99\", \"Chromium\";v=\"102\", \"Google Chrome\";v=\"102\"',\n            'sec-ch-ua-mobile': '?0',\n            'sec-ch-ua-platform': '\"macOS\"',\n            'sec-fetch-dest': 'empty',\n            'sec-fetch-mode': 'cors',\n            'sec-fetch-site': 'none',\n            'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.0.0 Safari/537.36',\n        }\n        param = {\n            'sessionId': '441df692-afea-4a54-8aff-f5f20fd34f12',\n            'algorithmCode': 'shazam_v2',\n            'duration': '6',\n            'rawdata': _get_ncm_base64(audio_fp),\n            'times': '2',\n            'decrypt': '1'\n        }\n        result = requests.post(\n            'https://interface.music.163.com/api/music/audio/match',\n            headers=header,\n            params=param\n        ).json()\n        if result['code'] != 200:\n            raise requests.HTTPError\n        if not (data := result['data']['result']):\n            raise requests.HTTPError\n\n        result_list: list[RecognizeResult] = []\n        for datum in data:\n            song = datum['song']\n            result_list.append(\n                RecognizeResult(\n                    title=song['name'],\n                    artist=[artist['name'] for artist in song['artists']],\n                    album=song['album']['name'],\n                    url=f'https://music.163.com/#/song?id={song[\"id\"]}',\n                    pic_url=song['album']['picUrl'],\n                    recognizer_name=self.name\n                )\n            )\n        return result_list\n\n#<|file_sep|>/root/evaluation_autocompletion/DraCo/ReccEval/Source_Code//a13e/a13e-0.0.1/a13e/recognizer.py\nimport abc\nfrom pathlib import Path\nfrom typing import List\n\nfrom a13e.tag import SongData\n\n\nclass RecognizeResult(SongData):\n    url: str\n    recognizer_name: str\n\n\nclass BaseRecognizer(abc.ABC):\n    \"\"\"Abstract base recognizer.\n\n    Inherit this abstract base class and decorate with the PluginManager.register\n    decorator to 'enable' this recognizer. A recognizer should only correspond to one API platform\n\n    Methods:\n        recognize: The method actually called by the external function.\n\n    Attributes:\n        name: It is used to distinguish the recognizers.\n        The name is generally the API platform used and uses Pascal nomenclature.\n    \"\"\"\n\n    @abc.abstractmethod\n    def recognize(self, audio_fp: Path, **kwargs) -> List[RecognizeResult]:\n        \"\"\"The method actually called by the external function.\n\n        Args:\n            audio_fp: Audio file path.\n            **kwargs: Recognizer extra parameters, if needed\n\n        Returns:\n            List of recognition results.\n        \"\"\"\n        raise NotImplementedError\n\n    @property\n    @abc.abstractmethod\n    def name(self) -> str:\n        \"\"\"It is used to distinguish the recognizers.\n        The name is generally the API platform used and uses Pascal nomenclature.\"\"\"\n        raise NotImplementedError\n\n\n\n#<|file_sep|>/root/evaluation_autocompletion/DraCo/ReccEval/Source_Code//a13e/a13e-0.0.1/a13e/utils.py\n    data = get_audio_data(audio_fp)\n    if data['streams'][0]['sample_rate'] == sample_rate:\n        return audio_fp\n\n    temp_file_path = audio_fp.parent / f'{audio_fp.stem}-{sample_rate}MHz{audio_fp.suffix}'\n    subprocess.check_call(\n        [\n            'ffmpeg',\n            '-i',\n            str(audio_fp),\n            '-ac',\n            '2',\n            '-ar',\n            sample_rate,\n            '-y',\n            str(temp_file_path)\n        ],\n        stdout=subprocess.DEVNULL,\n        stderr=subprocess.STDOUT\n    )\n    return temp_file_path\n\n\n@contextlib.contextmanager\ndef remove_file_context(fp: Path):\n    \"\"\"Delete the file when the context exits.\"\"\"\n    try:\n        yield\n    finally:\n        fp.unlink(missing_ok=True)\n\n\n@contextlib.contextmanager\ndef temp_file_context(temp_fp: Path, *args, **kwargs) -> Generator[IO, Any, None]:\n    \"\"\"Files are opened or created on entry to the context and deleted on exit.\n\n    Args:\n        temp_fp: File path.\n        args: The variable length parameter of Path.open.\n        **kwargs: Keyword arguments to Path.open.\n\n    Returns:\n        File object.\n    \"\"\"\n    with remove_file_context(temp_fp), temp_fp.open(*args, **kwargs) as f:\n        yield f\n\n\n@contextlib.contextmanager\ndef chdir_context(workdir: Path) -> Generator[Any, Any, None]:\n#<|file_sep|>/root/evaluation_autocompletion/DraCo/ReccEval/Source_Code//a13e/a13e-0.0.1/setup.py\nfrom setuptools import setup\n\nif __name__ == '__main__':\n    setup()\n\n#<|file_sep|>/root/evaluation_autocompletion/DraCo/ReccEval/Source_Code//a13e/a13e-0.0.1/a13e/__main__.py\nimport argparse\nimport sys\nfrom pathlib import Path\n\nimport a13e\nfrom a13e.json_helper import dump_json\n\n\ndef audio_file(args):\n    params = args.extra_params or dict()\n    if args.random:\n        result = (a13e.random_recognize(args.audio_file, name=args.recognize_name, **params))\n    else:\n        result = a13e.recognize(args.audio_file, name=args.recognize_name, **params)\n    if not result:\n        print('No recognition result found.')\n        sys.exit(1)\n    if args.set_tag:\n        a13e.set_tag(args.audio_file, result[0])\n    if args.output:\n        dump_json(args.output, result)\n    if args.silent:\n        print(result)\n\n    return result\n\n\nclass StoreDict(argparse.Action):\n    def __call__(self, parser, namespace, values, option_string=None):\n        kv = {}\n        if not isinstance(values, list):\n            values = (values,)\n        for value in values:\n            n, v = value.split('=')\n            kv[n] = v\n        setattr(namespace, self.dest, kv)\n\n\ndef main():\n    parser = argparse.ArgumentParser(prog='a13e')\n    parser.add_argument('audio_fp', type=Path, help='Audio file path.')\n    parser.add_argument('-v', '--version', action='version', version=f'%(prog)s {a13e.__version__}')\n    parser.add_argument('-s', '--silent', action='store_false', help='silent output.')\n    parser.add_argument('-n', '--recognize-name', nargs='*', help='specify the recognizer to use.')\n    parser.add_argument('-r', '--random', action='store_true', help='Randomly returns one from recognition results.')\n    parser.add_argument('-t', '--set-tag', action='store_true', help='assign the first result as a tag to the audio file.')\n    parser.add_argument('-o', '--output', type=Path, help='Output the result to a json file.')\n    parser.add_argument('--extra-params', nargs='*', action=StoreDict,\n                        help='Pass extra parameters required by some recognizers in the format of key=value')\n    parser.set_defaults(func=audio_file)\n#<|file_sep|>/root/evaluation_autocompletion/DraCo/ReccEval/Source_Code//a13e/a13e-0.0.1/a13e/utils.py\ndef process_error_decorator(\n        exception: Optional[Exception] = None\n) -> Callable[[OriginalFunc], OriginalFunc]:\n    def decorator(func: OriginalFunc) -> OriginalFunc:\n        @wraps(func)\n        def wrapper(*args: Param.args, **kwargs: Param.kwargs) -> RetType:\n            try:\n                return func(*args, **kwargs)\n            except subprocess.CalledProcessError as e:\n                print(e.returncode, e.output.decode())\n                if exception:\n                    raise exception\n\n        return wrapper\n\n    return decorator\n\n\n@process_error_decorator(ProcessError())\ndef get_audio_data(audio_fp: Path) -> Any:\n    \"\"\"Get audio data via ffprobe.\n    Args:\n        audio_fp: Audio file path\n\n    Return:\n        Audio data Python object (use json.loads)\n    Raises:\n        ProcessError: Will raise if FFmpeg return code is non-zero.\n\n    \"\"\"\n    output = subprocess.check_output(\n        [\n            'ffprobe',\n            '-v',\n            'error',\n            '-hide_banner',\n            '-print_format',\n            'json',\n            '-show_format',\n            '-show_streams',\n            str(audio_fp),\n        ],\n        stderr=subprocess.STDOUT\n    )\n    return json.loads(output)\n\n\n@process_error_decorator(ProcessError())\ndef resample(audio_fp: Path, *, sample_rate: str) -> Path:\n    \"\"\"Resample the audio to single-channel audio at the specified sample rate.\n#<|file_sep|>/root/evaluation_autocompletion/DraCo/ReccEval/Source_Code//a13e/a13e-0.0.1/a13e/exception.py\nclass BaseSongRecognizeException(Exception):\n    ...\n\n\nclass ProcessError(BaseSongRecognizeException):\n    \"\"\"subprocess error\"\"\"\n\n\n<|file_sep|>neteasemusic.py\n<|fim_prefix|>import subprocess\nimport sys\nfrom pathlib import Path\nfrom typing import List\n\nimport requests\n\nfrom a13e.exception import ProcessError\nfrom a13e.plugin import PluginRegister\nfrom a13e.recognizer import BaseRecognizer, RecognizeResult\nfrom a13e.utils import resample, chdir_context, process_error_decorator\ntry:\n    from importlib.resources import files\nexcept ImportError:\n    from importlib_resources import files\n\nWIN_BINARY = 'ncm_base64-win.exe'\nLINUX_BINARY = 'ncm_base64-linux'\nMACOS_BINARY = 'ncm_base64-macos'\n\nBINARY_FILE_NAME: str\nif sys.platform.startswith('win'):\n    BINARY_FILE_NAME = WIN_BINARY\nelif sys.platform.startswith('linux'):\n    BINARY_FILE_NAME = LINUX_BINARY\nelif sys.platform.startswith('darwin'):\n    BINARY_FILE_NAME = MACOS_BINARY\nelse:\n    raise RuntimeError\n\nBINARY_FILE_PATH = files('a13e.binary').joinpath(BINARY_FILE_NAME)\n\n\n@process_error_decorator(ProcessError())\ndef _get_ncm_base64(audio_fp: Path):\n    resolve = audio_fp.resolve()\n    temp_fp = resample(resolve, sample_rate='48000')\n    with chdir_context(Path(__file__).parent):\n        output = subprocess.check_output(\n            list(map(str, [BINARY_FILE_PATH, temp_fp])),\n            stderr=subprocess.STDOUT\n        )\n        output_list: List[str] = output.decode().strip().splitlines()\n        if temp_fp != resolve:\n            temp_fp.unlink<|fim_suffix|><|fim_middle|>"

    # model_inputs = TOKENIZER([input_text], return_tensors="pt").to(device)

    # # Use `max_new_tokens` to control the maximum output length.
    # generated_ids = MODEL.generate(model_inputs.input_ids, max_new_tokens=10, do_sample=False)[0]
    # # The generated_ids include prompt_ids, we only need to decode the tokens after prompt_ids.
    # output_text = TOKENIZER.decode(generated_ids[len(model_inputs.input_ids[0]):], skip_special_tokens=True)

    # print(f"Prompt: {input_text}\n\nGenerated text: {output_text}")