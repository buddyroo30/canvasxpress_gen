"""
Refactored Flask application for CanvasXpress Generation System.

This version uses the new modular architecture with proper imports and
professional code organization as required by JOSS reviewers.
"""

from flask import Flask, render_template, request, redirect, url_for, flash, abort, session, jsonify, send_from_directory, send_file
from werkzeug.utils import secure_filename
import os
import sys
import re
import datetime
import time
import json
import urllib.parse
import boto3
from tabulate import tabulate
import numpy as np
from dotenv import load_dotenv
from typing import Dict, Any, List, Optional, Tuple

# Import our new modular components
from src.canvasxpress_gen.llm import LLMService
from src.canvasxpress_gen.rag import RetrievalService
from src.canvasxpress_gen.utils import (
    JSONSimilarity, ConfigValidator,
    load_json_file, empty, random_password,
    clean_llm_response_text, parse_file,
    getSiteMinderUser, getSMRedirectUrl
)
from AESCipher import AESCipher

# Load environment variables
load_dotenv()


class CanvasXpressApp:
    """
    Main application class for CanvasXpress Generation System.
    
    This class encapsulates the Flask application and provides a clean
    interface for the CanvasXpress generation functionality.
    """
    
    def __init__(self):
        """Initialize the CanvasXpress application."""
        self.app = Flask(__name__)
        self.dev_flag = self._get_dev_flag()
        self.sm_validation = self._get_sm_validation()
        self.validated_cookies = {}
        
        # Initialize services
        self.llm_service = None
        self.retrieval_service = None
        self.config_validator = ConfigValidator()
        
        # Configuration
        self._setup_app_config()
        self._setup_file_paths()
        self._initialize_services()
        self._register_routes()
    
    def _get_dev_flag(self) -> bool:
        """Get development flag from environment."""
        dev_flag = os.environ.get("DEV")
        return dev_flag == 'True' if dev_flag else False
    
    def _get_sm_validation(self) -> bool:
        """Get SiteMinder validation flag from environment."""
        sm_val = os.environ.get('SMVAL')
        return sm_val == 'True' if sm_val else False
    
    def _setup_app_config(self) -> None:
        """Setup Flask application configuration."""
        self.app.config['SECRET_KEY'] = random_password(16)
        self.app.config['UPLOAD_FOLDER'] = "/tmp"
        self.aes = AESCipher(self.app.config['SECRET_KEY'])
    
    def _setup_file_paths(self) -> None:
        """Setup file paths based on development flag."""
        if self.dev_flag:
            self.prompt_file = "prompt_dev.md"
            self.schema_info_file = "/root/.cache/schema_dev.txt"
            self.docs_file = "doc_dev.json"
            self.examples_file = "all_few_shots_dev.json"
        else:
            self.prompt_file = "prompt.md"
            self.schema_info_file = "/root/.cache/schema.txt"
            self.docs_file = "doc.json"
            self.examples_file = "all_few_shots.json"
        
        # Validate required files exist
        if not os.path.exists(self.schema_info_file):
            print(f"Schema file not found: {self.schema_info_file}")
            print("Please generate the schema file first; exiting...")
            sys.exit(1)
    
    def _initialize_services(self) -> None:
        """Initialize LLM and RAG services."""
        try:
            # Initialize LLM service
            self.llm_service = LLMService()
            
            # Load and validate LLM models
            llm_models_file = "/root/.cache/llm_models.json"
            if os.path.exists(llm_models_file):
                self.llm_models = load_json_file(llm_models_file)
                self.llm_models_client = self._convert_model_data(self.llm_models)
            else:
                print(f"LLM models file not found: {llm_models_file}")
                print("Please generate the LLM models file first; exiting...")
                sys.exit(1)
            
            # Initialize direct PyMilvus connection (same as vectorize_schema_few_shots.py)
            from pymilvus import MilvusClient
            from pymilvus.model.hybrid import BGEM3EmbeddingFunction
            
            self.vector_db_file = "/root/.cache/canvasxpress_llm_dev.db" if self.dev_flag else "/root/.cache/canvasxpress_llm.db"
            
            if os.path.exists(self.vector_db_file):
                # Direct connection using same approach as vectorize_schema_few_shots.py
                self.milvus_client = MilvusClient(self.vector_db_file)
                self.bge_m3_ef = BGEM3EmbeddingFunction(
                    model_name='BAAI/bge-m3',
                    device='cpu',
                    use_fp16=False
                )
                print(f"Direct PyMilvus connection established: {self.vector_db_file}")
                self.retrieval_service = "direct_milvus"  # Flag for direct connection
            else:
                print(f"Warning: Vector database not found: {self.vector_db_file}")
                print("Please run 'make build_vector_db' first")
                self.retrieval_service = None
            
            print("Services initialized successfully")
            
        except Exception as e:
            print(f"Error initializing services: {e}")
            # Continue without RAG if it fails
            self.retrieval_service = None
    
    def _convert_model_data(self, models: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert model data for client consumption."""
        client_models = []
        for model_name, model_info in models.items():
            client_model = {
                'value': model_name,  # JavaScript expects 'value' property
                'text': model_info.get('description', model_name),  # JavaScript expects 'text' property
                'type': model_info.get('type', 'unknown'),
                'provider': model_info.get('provider', 'unknown')
            }
            client_models.append(client_model)
        return client_models
    
    def _register_routes(self) -> None:
        """Register Flask routes."""
        # Before request handler
        self.app.before_request(self._before_request_func)
        
        # Main routes
        self.app.route('/')(self._home)
        self.app.route('/userinfo', methods=['GET', 'POST'])(self._userinfo)
        self.app.route('/getenv', methods=['GET', 'POST'])(self._getenv)
        self.app.route('/get_few_shots', methods=['GET', 'POST'])(self._get_few_shots)
        self.app.route('/ask', methods=['GET', 'POST'])(self._ask)
        self.app.route('/ask_generic', methods=['GET', 'POST'])(self._ask_generic)
    
    def _before_request_func(self) -> Optional[Any]:
        """Handle SiteMinder authentication before requests."""
        req_ep = request.endpoint or ''
        print(f'In before_request_func, endpoint: {req_ep}')
        
        if self.sm_validation:
            cur_sm_validation_vals = getSiteMinderUser(request, self.validated_cookies)
            if cur_sm_validation_vals is None or empty(cur_sm_validation_vals.get('User')):
                return redirect(getSMRedirectUrl(request))
        
        return None
    
    def _home(self) -> str:
        """Home page route."""
        return render_template('index.html', models_arr=self.llm_models_client)
    
    def _userinfo(self) -> str:
        """User information route."""
        cur_user_info = {}
        if self.sm_validation:
            cur_sm_validation_vals = getSiteMinderUser(request, self.validated_cookies)
            cur_user_info['uid'] = cur_sm_validation_vals.get('User', 'NA')
            cur_user_info['bmsid'] = cur_sm_validation_vals.get('bmsid', 'NA')
        else:
            cur_user_info['uid'] = 'NA'
            cur_user_info['bmsid'] = 'NA'
        
        return json.dumps(cur_user_info)
    
    def _getenv(self) -> str:
        """Environment variables route."""
        all_env_txt = ""
        for name, value in os.environ.items():
            all_env_txt += f"{name}: {value}\n"
        return f"<plaintext>{all_env_txt}</plaintext>"
    
    def _get_few_shots(self) -> str:
        """Get few-shot examples route."""
        prompt = request.values.get('prompt', '').strip()
        num = request.values.get('num')
        format_type = request.values.get('format', 'text')
        filter_prompt = request.values.get('filter_prompt') == 'True'
        
        if format_type not in ['text', 'json']:
            format_type = 'text'
        
        try:
            if self.retrieval_service == "direct_milvus" and hasattr(self, 'milvus_client'):
                if num == 'all':
                    # Get all examples using direct PyMilvus query
                    return self._get_all_few_shots_direct(format_type)
                else:
                    # Get specific number of examples using direct PyMilvus search
                    num_shots = int(num) if num else 5
                    return self._get_few_shots_direct(prompt, num_shots, filter_prompt, format_type)
            else:
                return "RAG service not available"
                
        except Exception as e:
            return f"Error retrieving few-shot examples: {str(e)}"
    
    def _get_all_few_shots_direct(self, format_type: str = 'text') -> str:
        """Get all few-shot examples using direct PyMilvus query."""
        try:
            all_res = self.milvus_client.query(
                "few_shot_examples",
                filter="id >= 0",
                output_fields=["config", "configEnglish", "headers", "id"]
            )
            
            few_shot_txt = ""
            few_shot_obj = []
            
            for hit in all_res:
                cur_config = hit['config'].replace("\n", " ")
                cur_english_config = hit['configEnglish'].replace("\n", " ")
                cur_headers_column_names = hit['headers'].replace("\n", " ")
                
                if format_type == 'text':
                    few_shot_txt += f"English Text: {cur_english_config}; Headers/Column Names: {cur_headers_column_names}, Answer: {cur_config}\n"
                elif format_type == 'json':
                    cur_rec = {
                        'English Text': cur_english_config,
                        'Headers/Column Names': cur_headers_column_names,
                        'Answer': cur_config
                    }
                    few_shot_obj.append(cur_rec)
            
            if format_type == 'json':
                return json.dumps(few_shot_obj)
            
            return few_shot_txt
            
        except Exception as e:
            raise Exception(f"Failed to get all few-shot examples: {e}")
    
    def _get_few_shots_direct(self, prompt: str, num_few_shots: int = 25, filter_prompt: bool = False, format_type: str = 'text') -> str:
        """Get few-shot examples using direct PyMilvus search."""
        try:
            in_num_few_shots = num_few_shots
            if filter_prompt:
                num_few_shots = num_few_shots + 1
            
            prompt = prompt.replace("\n", " ")
            queries = [prompt]
            
            # Encode query using BGE-M3
            query_embeddings = self.bge_m3_ef.encode_queries(queries)
            
            # Search in PyMilvus
            res = self.milvus_client.search(
                collection_name="few_shot_examples",
                data=[query_embeddings["dense"][0]],
                limit=num_few_shots,
                output_fields=["config", "configEnglish", "headers", "id"],
            )
            
            few_shot_txt = ""
            few_shot_obj = []
            few_shots_ct = 0
            
            for hits in res:
                for hit in hits:
                    if few_shots_ct < in_num_few_shots:
                        cur_config = hit['entity']['config'].replace("\n", " ")
                        cur_english_config = hit['entity']['configEnglish'].replace("\n", " ")
                        
                        # Filter out the exact prompt if requested
                        if filter_prompt and prompt == cur_english_config:
                            continue
                            
                        cur_headers_column_names = hit['entity']['headers'].replace("\n", " ")
                        
                        if format_type == 'text':
                            few_shot_txt += f"English Text: {cur_english_config}; Headers/Column Names: {cur_headers_column_names}, Answer: {cur_config}\n"
                        elif format_type == 'json':
                            cur_rec = {
                                'English Text': cur_english_config,
                                'Headers/Column Names': cur_headers_column_names,
                                'Answer': cur_config
                            }
                            few_shot_obj.append(cur_rec)
                        
                        few_shots_ct += 1
            
            if format_type == 'json':
                return json.dumps(few_shot_obj)
            
            return few_shot_txt
            
        except Exception as e:
            raise Exception(f"Failed to get few-shot examples: {e}")
    
    def _ask(self) -> str:
        """Main CanvasXpress generation route."""
        try:
            # Parse request data
            request_data = self._parse_ask_request()
            if 'error' in request_data:
                return json.dumps(request_data['error'])
            
            # Handle special prompts
            special_response = self._handle_special_prompts(
                request_data['prompt'], 
                request_data['orig_prompt'], 
                request_data['datetime']
            )
            if special_response:
                return self._format_response(special_response, request_data)
            
            # Generate CanvasXpress configuration
            config_response = self._generate_canvasxpress_config(request_data)
            return self._format_response(config_response, request_data)
            
        except Exception as e:
            error_resp = {
                'text': f"Unexpected error: {str(e)}",
                'success': False,
                'config_generated_flag': False
            }
            return json.dumps(error_resp)
    
    def _parse_ask_request(self) -> Dict[str, Any]:
        """Parse the /ask request parameters."""
        # Get data file contents
        datafile_contents, header_row, datafilename = self._parse_data_file()
        if not datafile_contents:
            return {
                'error': {
                    'text': "Error: you must upload a data file to visualize or pass in a header",
                    'success': False,
                    'config_generated_flag': False
                }
            }
        
        # Parse request parameters
        prompt = request.values.get('prompt', '').strip()
        if not prompt:
            return {
                'error': {
                    'text': "Error: you must provide a description of the visualization you want",
                    'success': False,
                    'config_generated_flag': False
                }
            }
        
        return {
            'datafile_contents': datafile_contents,
            'header_row': header_row,
            'datafilename': datafilename,
            'prompt': prompt,
            'orig_prompt': prompt,
            'model': request.values.get('model', 'gpt-4-32k'),
            'max_new_tokens': int(request.values.get('max_new_tokens', 1024)),
            'topp': float(request.values.get('topp', 1.0)),
            'temperature': float(request.values.get('temperature', 0.0)),
            'presence_penalty': float(request.values.get('presence_penalty', 0.0)),
            'frequency_penalty': float(request.values.get('frequency_penalty', 0.0)),
            'filter_prompt_from_few_shots': request.values.get('filter_prompt_from_few_shots') == 'True',
            'config_only': request.values.get('config_only') == 'True',
            'num_few_shots': int(request.values.get('num_few_shots', 25)),
            'target': request.values.get('target'),
            'client': request.values.get('client'),
            'callback': request.values.get('callback'),
            'datetime': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        }
    
    def _parse_data_file(self) -> Tuple[List[List[str]], List[str], Optional[str]]:
        """Parse data file from request."""
        datafile_contents = []
        header_row = []
        datafilename = None
        
        # Try different sources for data
        in_datafile_contents = request.values.get('datafile_contents')
        in_header = request.values.get('header')
        
        if in_datafile_contents:
            datafile_contents = json.loads(in_datafile_contents)
        elif in_header:
            datafile_contents = json.loads(in_header)
        elif 'datafile_upload' in request.files and request.files['datafile_upload'].filename:
            datafile = request.files['datafile_upload']
            datafilename = secure_filename(datafile.filename)
            upload_filepath = os.path.join(self.app.config['UPLOAD_FOLDER'], datafilename)
            datafile.save(upload_filepath)
            datafile_contents = parse_file(upload_filepath)
        
        if datafile_contents:
            header_row = datafile_contents[0]
        
        return datafile_contents, header_row, datafilename
    
    def _handle_special_prompts(self, prompt: str, orig_prompt: str, datetime_str: str) -> Optional[Dict[str, Any]]:
        """Handle special prompt responses."""
        special_responses = {
            'Thumbs down': 'Thank-you for giving negative feedback, we will use it to improve future performance.',
            'Thumbs up': 'Thank-you for giving positive feedback, we will use it to improve future performance.',
            'Help': 'You can generate visualizations by describing them in plain English, e.g. boxplot with legend at top right, and uploading a file of data to graph.'
        }
        
        if prompt in special_responses:
            return {
                'success': True,
                'text': special_responses[prompt],
                'config_generated_flag': False,
                'prompt': orig_prompt,
                'datetime': datetime_str
            }
        
        return None
    
    def _generate_canvasxpress_config(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate CanvasXpress configuration using LLM and direct PyMilvus RAG."""
        start_time = time.time()
        
        try:
            # Get few-shot examples using direct PyMilvus retrieval
            few_shot_examples = ""
            if self.retrieval_service == "direct_milvus" and hasattr(self, 'milvus_client'):
                few_shot_examples = self._get_few_shots_direct(
                    request_data['prompt'],
                    request_data['num_few_shots'],
                    request_data['filter_prompt_from_few_shots'],
                    'text'
                )
            
            # Load schema information
            with open(self.schema_info_file, 'r') as f:
                schema_info = f.read()
            
            # Generate configuration using LLM service
            try:
                config_dict = self.llm_service.generate_json_config(
                    prompt=request_data['prompt'],
                    schema_info=schema_info,
                    few_shot_examples=few_shot_examples,
                    model=request_data['model']
                )
                
                # Validate the generated configuration
                if not self.config_validator.validate_config(config_dict):
                    return {
                        'text': f"Error: Generated configuration is invalid",
                        'success': False,
                        'config_generated_flag': False
                    }
                
            except Exception as e:
                return {
                    'text': f"Error generating configuration: {str(e)}",
                    'success': False,
                    'config_generated_flag': False
                }
            
            end_time = time.time()
            generation_time = end_time - start_time
            
            response = {
                'success': True,
                'config': config_dict,
                'config_generated_flag': True,
                'total_time_taken': generation_time,
                'prompt': request_data['orig_prompt'],
                'datetime': request_data['datetime']
            }
            
            if not request_data['config_only']:
                response['datafilename'] = request_data['datafilename']
                response['data'] = request_data['datafile_contents']
                response['header'] = request_data['header_row']
            
            return response
            
        except Exception as e:
            return {
                'text': f"Error generating configuration: {str(e)}",
                'success': False,
                'config_generated_flag': False
            }
    
    def _format_response(self, response: Dict[str, Any], request_data: Dict[str, Any]) -> str:
        """Format the final response."""
        # Add optional fields
        if request_data.get('target'):
            response['target'] = request_data['target']
        if request_data.get('client'):
            response['client'] = request_data['client']
        
        response_json = json.dumps(response)
        
        # Handle JSONP callback
        if request_data.get('callback'):
            return f"{request_data['callback']}({response_json})"
        else:
            return response_json
    
    def _ask_generic(self) -> str:
        """Generic LLM query route."""
        try:
            prompt = request.values.get('prompt', '').strip()
            if not prompt:
                error_resp = {
                    'text': "Error: you must provide a prompt for the LLM",
                    'success': False
                }
                return json.dumps(error_resp)
            
            model = request.values.get('model', 'gpt-4-32k')
            max_new_tokens = int(request.values.get('max_new_tokens', 1024))
            temperature = float(request.values.get('temperature', 0.0))
            top_p = float(request.values.get('topp', 1.0))
            
            start_time = time.time()
            
            # Use LLM service for generic generation
            result = self.llm_service.generate_text(
                prompt=prompt,
                model_name=model,
                temperature=temperature,
                max_tokens=max_new_tokens,
                top_p=top_p
            )
            
            end_time = time.time()
            
            if result.success:
                response = {
                    'success': True,
                    'text': result.text,
                    'total_time_taken': end_time - start_time,
                    'datetime': datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                }
            else:
                response = {
                    'success': False,
                    'text': f"Error: {result.error}"
                }
            
            callback = request.values.get('callback')
            response_json = json.dumps(response)
            
            if callback:
                return f"{callback}({response_json})"
            else:
                return response_json
                
        except Exception as e:
            error_resp = {
                'text': f"Unexpected error: {str(e)}",
                'success': False
            }
            return json.dumps(error_resp)
    
    def run(self, host: str = '0.0.0.0', port: int = 5000, debug: bool = False) -> None:
        """Run the Flask application."""
        self.app.run(host=host, port=port, debug=debug)


# Create and run the application
if __name__ == '__main__':
    try:
        canvas_app = CanvasXpressApp()
        print("CanvasXpress Generation System starting...")
        canvas_app.run(debug=canvas_app.dev_flag)
    except Exception as e:
        print(f"Failed to start application: {e}")
        sys.exit(1)