"""
Evaluation Case Generator Service
Generates synthetic evaluation cases from prompts with parameters.
Implements Story 2: Generate Evaluation Cases from Prompt Parameters
"""
import random
import uuid
from typing import List, Dict, Any, Optional
from core.models import SystemPrompt
from .unified_llm_provider import get_llm_provider


class EvaluationCaseGenerator:
    """Service for generating synthetic evaluation cases from prompts"""
    
    def __init__(self):
        self.llm_provider = get_llm_provider()
        
        # Parameter value generators based on common parameter names
        self.parameter_generators = {
            'user_name': self._generate_user_names,
            'customer_name': self._generate_user_names,
            'name': self._generate_user_names,
            'customer_email': self._generate_emails,
            'user_email': self._generate_emails,
            'email': self._generate_emails,
            'product_type': self._generate_product_types,
            'product_name': self._generate_product_names,
            'product': self._generate_product_names,
            'order_id': self._generate_order_ids,
            'order_number': self._generate_order_ids,
            'user_question': self._generate_user_questions,
            'question': self._generate_user_questions,
            'issue': self._generate_user_questions,
            'problem': self._generate_user_questions,
            'company_name': self._generate_company_names,
            'location': self._generate_locations,
            'date': self._generate_dates,
            'amount': self._generate_amounts,
            'phone': self._generate_phone_numbers,
            'phone_number': self._generate_phone_numbers,
            # Email-specific parameters
            'email_content': self._generate_email_content,
            'EMAIL_CONTENT': self._generate_email_content,
            'recipient_info': self._generate_recipient_info,
            'RECIPIENT_INFO': self._generate_recipient_info,
            'sender_info': self._generate_sender_info,
            'SENDER_INFO': self._generate_sender_info,
        }
    
    def generate_cases_preview(self, prompt: SystemPrompt, count: int = 5, dataset=None, persist_immediately: bool = False) -> List[Dict[str, Any]]:
        """
        Generate evaluation cases for preview (optionally saved to database)
        
        Args:
            prompt: SystemPrompt with parameters to generate cases for
            count: Number of cases to generate
            dataset: EvaluationDataset to save cases to (if persist_immediately=True)
            persist_immediately: If True, save cases to database immediately
            
        Returns:
            List of generated case dictionaries with preview_id, input_text, expected_output, parameters
        """
        if not prompt.parameters:
            prompt.extract_parameters()
        
        generated_cases = []
        
        for i in range(count):
            # Generate parameter values
            parameter_values = self._generate_parameter_values(prompt.parameters)
            
            # Substitute parameters in prompt content to create input text
            input_text = self._substitute_parameters(prompt.content, parameter_values)
            
            # Generate expected output using LLM
            expected_output = self._generate_expected_output(input_text, prompt.content)
            
            case = {
                'preview_id': str(uuid.uuid4()),  # Temporary ID for frontend tracking
                'input_text': input_text,
                'expected_output': expected_output,
                'parameters': parameter_values,
                'prompt_content': prompt.content
            }
            
            # Persist immediately if requested
            if persist_immediately and dataset:
                from core.models import EvaluationCase
                db_case = EvaluationCase.objects.create(
                    dataset=dataset,
                    input_text=input_text,
                    expected_output=expected_output,
                    context=parameter_values  # Store parameters in context
                )
                case['id'] = db_case.id  # Add database ID to case
                case['persisted'] = True
            else:
                case['persisted'] = False
            
            generated_cases.append(case)
        
        return generated_cases
    
    def generate_cases_from_template(self, template: str, parameters: List[str], count: int = 5, dataset=None, persist_immediately: bool = False) -> List[Dict[str, Any]]:
        """
        Generate evaluation cases from a template string
        
        Args:
            template: Template string with {parameter} placeholders
            parameters: List of parameter names expected in the template
            count: Number of cases to generate
            dataset: EvaluationDataset to save cases to (if persist_immediately=True)
            persist_immediately: If True, save cases to database immediately
            
        Returns:
            List of generated case dictionaries with preview_id, generated_input, generated_output, parameters
        """
        generated_cases = []
        
        for i in range(count):
            # Generate parameter values
            parameter_values = self._generate_parameter_values(parameters)
            
            # Substitute parameters in template to create input text
            input_text = self._substitute_parameters(template, parameter_values)
            
            # Generate expected output using LLM
            expected_output = self._generate_expected_output_from_template(input_text, template)
            
            case = {
                'preview_id': str(uuid.uuid4()),  # Temporary ID for frontend tracking
                'generated_input': input_text,
                'generated_output': expected_output,
                'parameters': parameter_values,
                'template': template
            }
            
            # Persist immediately if requested
            if persist_immediately and dataset:
                from core.models import EvaluationCase
                db_case = EvaluationCase.objects.create(
                    dataset=dataset,
                    input_text=input_text,
                    expected_output=expected_output,
                    context=parameter_values  # Store parameters in context
                )
                case['id'] = db_case.id  # Add database ID to case
                case['persisted'] = True
            else:
                case['persisted'] = False
            
            generated_cases.append(case)
        
        return generated_cases
    
    def regenerate_single_case(self, prompt: SystemPrompt, existing_case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Regenerate a single case with new parameter values
        
        Args:
            prompt: SystemPrompt to regenerate case for
            existing_case_data: Previous case data to replace
            
        Returns:
            New case dictionary
        """
        if not prompt.parameters:
            prompt.extract_parameters()
        
        # Generate new parameter values (different from existing)
        new_parameter_values = self._generate_parameter_values(prompt.parameters)
        
        # Try to ensure at least one parameter is different from existing
        max_attempts = 5
        attempt = 0
        existing_params = existing_case_data.get('parameters', {})
        
        while attempt < max_attempts:
            if any(new_parameter_values.get(key) != existing_params.get(key) 
                   for key in prompt.parameters):
                break
            new_parameter_values = self._generate_parameter_values(prompt.parameters)
            attempt += 1
        
        # Substitute parameters in prompt content
        input_text = self._substitute_parameters(prompt.content, new_parameter_values)
        
        # Generate expected output
        expected_output = self._generate_expected_output(input_text, prompt.content)
        
        return {
            'preview_id': existing_case_data.get('preview_id', str(uuid.uuid4())),
            'input_text': input_text,
            'expected_output': expected_output,
            'parameters': new_parameter_values,
            'prompt_content': prompt.content
        }
    
    def update_case_parameters(self, prompt: SystemPrompt, case_data: Dict[str, Any], 
                              new_parameters: Dict[str, str]) -> Dict[str, Any]:
        """
        Update case with manually edited parameter values
        
        Args:
            prompt: SystemPrompt being used
            case_data: Existing case data
            new_parameters: Updated parameter values
            
        Returns:
            Updated case dictionary
        """
        # Validate that all required parameters are provided
        missing_params = set(prompt.parameters) - set(new_parameters.keys())
        if missing_params:
            raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")
        
        # Substitute new parameters in prompt content
        input_text = self._substitute_parameters(prompt.content, new_parameters)
        
        # Keep the same expected output initially, or regenerate if needed
        expected_output = case_data.get('expected_output')
        if not expected_output:
            expected_output = self._generate_expected_output(input_text, prompt.content)
        
        return {
            'preview_id': case_data.get('preview_id'),
            'input_text': input_text,
            'expected_output': expected_output,
            'parameters': new_parameters,
            'prompt_content': prompt.content
        }
    
    def regenerate_expected_output(self, prompt: SystemPrompt, case_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Regenerate expected output for a case with existing parameters
        
        Args:
            prompt: SystemPrompt being used
            case_data: Case data with parameters
            
        Returns:
            Updated case dictionary with new expected output
        """
        input_text = case_data['input_text']
        new_expected_output = self._generate_expected_output(input_text, prompt.content)
        
        updated_case = case_data.copy()
        updated_case['expected_output'] = new_expected_output
        
        return updated_case
    
    def _generate_parameter_values(self, parameters: List[str]) -> Dict[str, str]:
        """Generate realistic values for the given parameters"""
        parameter_values = {}
        
        for param in parameters:
            # Try to find a specific generator for this parameter
            generator = None
            param_lower = param.lower()
            
            # Check for exact matches first
            if param_lower in self.parameter_generators:
                generator = self.parameter_generators[param_lower]
            else:
                # Check for partial matches
                for key_pattern, gen_func in self.parameter_generators.items():
                    if key_pattern in param_lower:
                        generator = gen_func
                        break
            
            if generator:
                parameter_values[param] = generator()
            else:
                # Fallback to generic text generation
                parameter_values[param] = self._generate_generic_value(param)
        
        return parameter_values
    
    def _substitute_parameters(self, content: str, parameter_values: Dict[str, str]) -> str:
        """Substitute parameter values in content"""
        result = content
        for param, value in parameter_values.items():
            result = result.replace(f'{{{param}}}', value)
        return result
    
    def _generate_expected_output(self, input_text: str, prompt_template: str) -> str:
        """Generate expected output using LLM"""
        try:
            # Create a prompt for the LLM to generate an appropriate response
            generation_prompt = f"""You are helping create evaluation cases for a customer service AI system.

Given this prompt template: {prompt_template}

And this specific input: {input_text}

Generate a high-quality, helpful response that a customer service assistant should provide. Make it professional, accurate, and customer-focused. Keep it concise but complete.

Response:"""
            
            # Run async method in sync context
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            response = loop.run_until_complete(self.llm_provider.generate(
                prompt=generation_prompt,
                max_tokens=150,
                temperature=0.7
            ))
            
            return response.strip()
            
        except Exception as e:
            # Fallback to a generic response if LLM fails
            return f"Thank you for your inquiry. I'll be happy to help you with your request."
    
    def generate_multiple_outputs(self, input_text: str, prompt_template: str, 
                                num_variations: int = 3, styles: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Generate multiple output variations for a single input"""
        if styles is None:
            styles = ['formal', 'friendly', 'detailed']
        
        outputs = []
        
        # Style-specific prompts
        style_instructions = {
            'formal': "Use a professional, formal tone with proper business language.",
            'friendly': "Use a warm, conversational tone while remaining professional.",
            'detailed': "Provide a comprehensive response with specific details and steps.",
            'empathetic': "Show understanding and empathy for the customer's situation.",
            'solution-focused': "Focus directly on solving the problem with clear action steps.",
            'explanatory': "Explain the reasoning behind your response and educate the customer."
        }
        
        for i, style in enumerate(styles[:num_variations]):
            try:
                # Create style-specific prompt
                style_instruction = style_instructions.get(style, style_instructions['formal'])
                
                generation_prompt = f"""You are helping create evaluation cases for a customer service AI system.

Given this prompt template: {prompt_template}

And this specific input: {input_text}

Generate a high-quality, helpful response that a customer service assistant should provide. 
{style_instruction}

Make it professional, accurate, and customer-focused. Keep it concise but complete.

Response:"""
                
                # Run async method in sync context
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                except RuntimeError:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)
                
                # Use different temperature for variety
                temperature = 0.6 + (i * 0.2)  # 0.6, 0.8, 1.0
                
                response = loop.run_until_complete(self.llm_provider.generate(
                    prompt=generation_prompt,
                    max_tokens=200,
                    temperature=min(temperature, 1.0)
                ))
                
                outputs.append({
                    'index': i,
                    'text': response.strip(),
                    'style': style
                })
                
            except Exception as e:
                # Fallback for this variation
                fallback_responses = {
                    'formal': "Thank you for contacting us. I'll be happy to assist you with your inquiry. Please allow me to review your request and provide you with the appropriate assistance.",
                    'friendly': "Hi there! Thanks for reaching out. I completely understand your concern and I'm here to help. Let me look into this for you right away.",
                    'detailed': "Thank you for your inquiry. I'll be happy to help you with your request. Let me provide you with a comprehensive solution to address your concern.",
                    'empathetic': "I understand this situation must be frustrating for you. I want to help resolve this matter as quickly as possible and ensure you have a positive experience.",
                    'solution-focused': "Let me help you resolve this issue right away. I'll walk you through the steps needed to address your concern.",
                    'explanatory': "I'd be happy to explain this process and help you understand how we can best assist you with your request."
                }
                
                outputs.append({
                    'index': i,
                    'text': fallback_responses.get(style, fallback_responses['formal']),
                    'style': style
                })
        
        return outputs
    
    def generate_cases_preview_with_variations(self, prompt: SystemPrompt, count: int = 5, 
                                              enable_variations: bool = True, dataset=None, persist_immediately: bool = False) -> List[Dict[str, Any]]:
        """Generate evaluation cases with multiple output variations for human selection"""
        if not prompt.parameters:
            prompt.extract_parameters()
        
        generated_cases = []
        
        for i in range(count):
            # Generate parameter values
            parameter_values = self._generate_parameter_values(prompt.parameters)
            
            # Substitute parameters in prompt content to create input text
            input_text = self._substitute_parameters(prompt.content, parameter_values)
            
            case = {
                'preview_id': str(uuid.uuid4()),
                'input_text': input_text,
                'parameters': parameter_values,
                'prompt_content': prompt.content
            }
            
            if enable_variations:
                # Generate multiple output variations
                output_variations = self.generate_multiple_outputs(
                    input_text=input_text,
                    prompt_template=prompt.content,
                    num_variations=3
                )
                case['output_variations'] = output_variations
                case['selected_output_index'] = None
                case['custom_output'] = None
                
                # For immediate persistence with variations, use first variation as default
                if persist_immediately and dataset and output_variations:
                    from core.models import EvaluationCase
                    default_output = output_variations[0]['text']
                    db_case = EvaluationCase.objects.create(
                        dataset=dataset,
                        input_text=input_text,
                        expected_output=default_output,
                        context=parameter_values
                    )
                    case['id'] = db_case.id
                    case['persisted'] = True
                    case['selected_output_index'] = 0  # Mark first variation as selected
                else:
                    case['persisted'] = False
            else:
                # Single output for backward compatibility
                expected_output = self._generate_expected_output(input_text, prompt.content)
                case['expected_output'] = expected_output
                
                # Persist immediately if requested
                if persist_immediately and dataset:
                    from core.models import EvaluationCase
                    db_case = EvaluationCase.objects.create(
                        dataset=dataset,
                        input_text=input_text,
                        expected_output=expected_output,
                        context=parameter_values
                    )
                    case['id'] = db_case.id
                    case['persisted'] = True
                else:
                    case['persisted'] = False
            
            generated_cases.append(case)
        
        return generated_cases
    
    def _generate_expected_output_from_template(self, input_text: str, template: str) -> str:
        """Generate expected output for template-based generation"""
        try:
            # Create a prompt for the LLM to generate an appropriate response
            generation_prompt = f"""You are helping create evaluation cases for a customer service AI system.

Given this template: {template}

And this specific input scenario: {input_text}

Generate a high-quality, helpful response that a customer service assistant should provide for this scenario. Make it professional, accurate, and customer-focused. Keep it concise but complete.

Response:"""
            
            # Run async method in sync context
            import asyncio
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            
            response = loop.run_until_complete(self.llm_provider.generate(
                prompt=generation_prompt,
                max_tokens=150,
                temperature=0.7
            ))
            
            return response.strip()
            
        except Exception as e:
            # Fallback to a generic response if LLM fails
            return f"Thank you for your inquiry. I'll be happy to help you with your request."
    
    # Parameter value generators
    def _generate_user_names(self) -> str:
        """Generate realistic user names"""
        first_names = [
            'John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'James', 'Ashley',
            'Robert', 'Jessica', 'William', 'Amanda', 'Christopher', 'Stephanie',
            'Daniel', 'Jennifer', 'Matthew', 'Lisa', 'Anthony', 'Mary'
        ]
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller',
            'Davis', 'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Gonzalez',
            'Wilson', 'Anderson', 'Thomas', 'Taylor', 'Moore', 'Jackson', 'Martin'
        ]
        return f"{random.choice(first_names)} {random.choice(last_names)}"
    
    def _generate_emails(self) -> str:
        """Generate realistic email addresses"""
        domains = ['gmail.com', 'yahoo.com', 'hotmail.com', 'outlook.com', 'company.com']
        prefixes = ['user', 'customer', 'john.doe', 'jane.smith', 'contact', 'info']
        numbers = random.randint(1, 999) if random.random() < 0.3 else ''
        
        prefix = random.choice(prefixes)
        domain = random.choice(domains)
        
        return f"{prefix}{numbers}@{domain}"
    
    def _generate_product_types(self) -> str:
        """Generate product categories"""
        products = [
            'laptop', 'smartphone', 'tablet', 'desktop computer', 'headphones',
            'smart watch', 'camera', 'printer', 'monitor', 'keyboard', 'mouse',
            'speaker', 'gaming console', 'smart TV', 'router', 'hard drive'
        ]
        return random.choice(products)
    
    def _generate_product_names(self) -> str:
        """Generate specific product names"""
        brands = ['TechPro', 'EliteMax', 'PowerCore', 'SmartEdge', 'UltraFast']
        models = ['X1', 'Pro', 'Elite', 'Max', 'Ultra', 'Plus', '2024', 'Series']
        numbers = [str(random.randint(100, 9999)) for _ in range(5)]
        
        brand = random.choice(brands)
        model = random.choice(models + numbers)
        
        return f"{brand} {model}"
    
    def _generate_order_ids(self) -> str:
        """Generate order IDs"""
        formats = [
            lambda: f"ORD-{random.randint(100000, 999999)}",
            lambda: f"{random.randint(10000000, 99999999)}",
            lambda: f"{''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=8))}",
        ]
        return random.choice(formats)()
    
    def _generate_user_questions(self) -> str:
        """Generate common customer questions"""
        questions = [
            'How do I reset my password?',
            'When will my order arrive?',
            'Can I return this item?',
            'How do I track my shipment?',
            'What is your refund policy?',
            'How do I cancel my subscription?',
            'Is this item still under warranty?',
            'How do I update my billing information?',
            'Can I change my delivery address?',
            'How do I contact technical support?',
            'What payment methods do you accept?',
            'How do I download my receipt?',
            'Is this product compatible with my device?',
            'How do I set up my account?',
            'What are your store hours?'
        ]
        return random.choice(questions)
    
    def _generate_company_names(self) -> str:
        """Generate company names"""
        companies = [
            'TechCorp Inc.', 'Global Solutions Ltd.', 'Innovative Systems',
            'Digital Dynamics', 'Smart Solutions Inc.', 'Future Tech Corp.',
            'NextGen Industries', 'Advanced Systems LLC', 'Elite Enterprises',
            'Prime Technologies'
        ]
        return random.choice(companies)
    
    def _generate_locations(self) -> str:
        """Generate locations"""
        cities = [
            'New York, NY', 'Los Angeles, CA', 'Chicago, IL', 'Houston, TX',
            'Phoenix, AZ', 'Philadelphia, PA', 'San Antonio, TX', 'San Diego, CA',
            'Dallas, TX', 'San Jose, CA', 'Austin, TX', 'Jacksonville, FL'
        ]
        return random.choice(cities)
    
    def _generate_dates(self) -> str:
        """Generate dates"""
        months = ['January', 'February', 'March', 'April', 'May', 'June',
                 'July', 'August', 'September', 'October', 'November', 'December']
        day = random.randint(1, 28)
        month = random.choice(months)
        year = random.choice([2023, 2024, 2025])
        
        return f"{month} {day}, {year}"
    
    def _generate_amounts(self) -> str:
        """Generate monetary amounts"""
        amount = random.uniform(10.99, 999.99)
        return f"${amount:.2f}"
    
    def _generate_phone_numbers(self) -> str:
        """Generate phone numbers"""
        area_code = random.randint(200, 999)
        first_three = random.randint(200, 999)
        last_four = random.randint(1000, 9999)
        
        return f"({area_code}) {first_three}-{last_four}"
    
    def _generate_email_content(self) -> str:
        """Generate realistic email content for testing"""
        email_templates = [
            "Hi there,\n\nI'm writing to follow up on my order placed last week. I haven't received any shipping confirmation yet and was wondering about the status. Could you please provide an update?\n\nThanks!",
            "Dear Customer Service,\n\nI received my order yesterday but there seems to be an issue with one of the items. The laptop case I ordered appears to be damaged. What should I do to get a replacement?\n\nBest regards",
            "Hello,\n\nI'm interested in returning a product I purchased last month. It doesn't fit my needs as expected. Can you walk me through the return process?\n\nThank you",
            "Hi,\n\nI'm having trouble accessing my account. When I try to log in, it says my password is incorrect, but I'm sure I'm using the right one. Can you help me reset it?\n\nAppreciate your help!",
            "Dear Support Team,\n\nI would like to cancel my subscription that's set to renew next week. I no longer need the service. Please confirm the cancellation.\n\nThanks for your assistance.",
            "Hello,\n\nI placed an order but realized I need to change the shipping address. Is it possible to update this before it ships? The new address is different from my billing address.\n\nPlease let me know!",
        ]
        return random.choice(email_templates)
    
    def _generate_recipient_info(self) -> str:
        """Generate recipient information"""
        recipients = [
            "John Smith, Premium Customer since 2020",
            "Sarah Johnson, Business Account Manager",
            "Mike Chen, VIP Member",
            "Emma Davis, Frequent Buyer",
            "Alex Rodriguez, Corporate Client",
            "Lisa Wang, Gold Tier Customer",
            "David Brown, New Customer",
            "Jennifer Wilson, Returning Customer",
        ]
        return random.choice(recipients)
    
    def _generate_sender_info(self) -> str:
        """Generate sender information"""
        senders = [
            "Customer Service Team",
            "Support Specialist - Maria Garcia",
            "Account Manager - James Thompson",
            "Technical Support - Kevin Liu",
            "Billing Department - Amanda Foster",
            "Returns Specialist - Ryan Murphy",
            "Senior Support Agent - Nicole Anderson",
            "Customer Success Manager - Tyler Brooks",
        ]
        return random.choice(senders)
    
    def _generate_generic_value(self, param_name: str) -> str:
        """Generate a generic value based on parameter name"""
        # Try to infer type from parameter name
        param_lower = param_name.lower()
        
        if any(word in param_lower for word in ['id', 'number', 'code']):
            return f"ID{random.randint(10000, 99999)}"
        elif any(word in param_lower for word in ['name', 'title']):
            return f"Sample {param_name.replace('_', ' ').title()}"
        elif any(word in param_lower for word in ['description', 'message', 'text', 'content']):
            return f"This is a sample {param_name.replace('_', ' ')}"
        else:
            return f"Value{random.randint(1, 100)}"