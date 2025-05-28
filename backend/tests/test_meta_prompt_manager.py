import pytest
import pytest_asyncio
from app.services.meta_prompt_manager import (
    MetaPromptManager,
    MetaPromptTemplate
)


@pytest.fixture
def meta_prompt_manager():
    """Fresh meta-prompt manager instance"""
    return MetaPromptManager()


@pytest.mark.asyncio
async def test_meta_prompt_manager_initialization(meta_prompt_manager):
    """Test that MetaPromptManager initializes with default templates"""
    assert len(meta_prompt_manager.templates) > 0
    assert len(meta_prompt_manager.scenario_mappings) > 0
    
    # Check default templates exist
    assert "general_rewrite" in meta_prompt_manager.templates
    assert "professional_email_rewrite" in meta_prompt_manager.templates
    assert "casual_email_rewrite" in meta_prompt_manager.templates
    assert "complaint_handling_rewrite" in meta_prompt_manager.templates
    assert "inquiry_response_rewrite" in meta_prompt_manager.templates


@pytest.mark.asyncio
async def test_get_meta_prompt_by_scenario(meta_prompt_manager):
    """Test getting meta-prompt by scenario type"""
    # Test professional scenario
    professional_prompt = await meta_prompt_manager.get_meta_prompt("professional")
    assert "business communication" in professional_prompt
    assert "professional" in professional_prompt.lower()
    
    # Test casual scenario
    casual_prompt = await meta_prompt_manager.get_meta_prompt("casual")
    assert "casual" in casual_prompt.lower()
    assert "friendly" in casual_prompt.lower()
    
    # Test complaint scenario
    complaint_prompt = await meta_prompt_manager.get_meta_prompt("complaint")
    assert "empathy" in complaint_prompt.lower()
    assert "complaint" in complaint_prompt.lower()


@pytest.mark.asyncio
async def test_get_meta_prompt_unknown_scenario(meta_prompt_manager):
    """Test getting meta-prompt for unknown scenario defaults to general"""
    unknown_prompt = await meta_prompt_manager.get_meta_prompt("unknown_scenario")
    general_prompt = await meta_prompt_manager.get_meta_prompt("general")
    
    # Should fall back to general template
    assert unknown_prompt == general_prompt


@pytest.mark.asyncio
async def test_apply_constraints_max_length(meta_prompt_manager):
    """Test applying max_length constraint"""
    constraints = {"max_length": 100}
    
    prompt = await meta_prompt_manager.get_meta_prompt("professional", constraints)
    
    assert "under 100 words" in prompt
    assert "Additional Constraints:" in prompt


@pytest.mark.asyncio
async def test_apply_constraints_tone(meta_prompt_manager):
    """Test applying tone constraint"""
    constraints = {"tone": "formal"}
    
    prompt = await meta_prompt_manager.get_meta_prompt("casual", constraints)
    
    assert "formal tone" in prompt
    assert "Additional Constraints:" in prompt


@pytest.mark.asyncio
async def test_apply_constraints_urgency_high(meta_prompt_manager):
    """Test applying high urgency constraint"""
    constraints = {"urgency": "high"}
    
    prompt = await meta_prompt_manager.get_meta_prompt("professional", constraints)
    
    assert "immediate action" in prompt
    assert "clear next steps" in prompt


@pytest.mark.asyncio
async def test_apply_constraints_urgency_low(meta_prompt_manager):
    """Test applying low urgency constraint"""
    constraints = {"urgency": "low"}
    
    prompt = await meta_prompt_manager.get_meta_prompt("professional", constraints)
    
    assert "thoughtful" in prompt
    assert "detailed" in prompt


@pytest.mark.asyncio
async def test_apply_constraints_audience(meta_prompt_manager):
    """Test applying audience constraint"""
    constraints = {"audience": "executives"}
    
    prompt = await meta_prompt_manager.get_meta_prompt("professional", constraints)
    
    assert "executives audience" in prompt


@pytest.mark.asyncio
async def test_apply_multiple_constraints(meta_prompt_manager):
    """Test applying multiple constraints simultaneously"""
    constraints = {
        "max_length": 50,
        "tone": "urgent",
        "audience": "clients"
    }
    
    prompt = await meta_prompt_manager.get_meta_prompt("professional", constraints)
    
    assert "under 50 words" in prompt
    assert "urgent tone" in prompt
    assert "clients audience" in prompt
    assert "Additional Constraints:" in prompt


@pytest.mark.asyncio
async def test_create_custom_template(meta_prompt_manager):
    """Test creating a custom meta-prompt template"""
    template_id = "test_custom_template"
    name = "Test Custom Template"
    description = "A custom template for testing"
    content = "This is a custom meta-prompt template for testing purposes."
    scenario_types = ["test_scenario", "custom_scenario"]
    constraints = {"test_constraint": True}
    
    template = await meta_prompt_manager.create_custom_template(
        template_id, name, description, content, scenario_types, constraints
    )
    
    # Verify template was created
    assert template.id == template_id
    assert template.name == name
    assert template.description == description
    assert template.template == content
    assert template.scenario_types == scenario_types
    assert template.constraints == constraints
    assert template.version == 1
    
    # Verify template was added to manager
    assert template_id in meta_prompt_manager.templates
    assert meta_prompt_manager.templates[template_id] == template
    
    # Verify scenario mappings were updated
    assert meta_prompt_manager.scenario_mappings["test_scenario"] == template_id
    assert meta_prompt_manager.scenario_mappings["custom_scenario"] == template_id


@pytest.mark.asyncio
async def test_update_template_effectiveness(meta_prompt_manager):
    """Test updating template effectiveness score"""
    template_id = "general_rewrite"
    new_score = 0.85
    
    await meta_prompt_manager.update_template_effectiveness(template_id, new_score)
    
    assert meta_prompt_manager.templates[template_id].effectiveness_score == new_score


@pytest.mark.asyncio
async def test_update_nonexistent_template_effectiveness(meta_prompt_manager):
    """Test updating effectiveness for non-existent template"""
    # Should not raise error
    await meta_prompt_manager.update_template_effectiveness("nonexistent", 0.5)


@pytest.mark.asyncio
async def test_get_best_template_for_scenario(meta_prompt_manager):
    """Test getting the most effective template for a scenario"""
    # Set different effectiveness scores
    await meta_prompt_manager.update_template_effectiveness("professional_email_rewrite", 0.9)
    await meta_prompt_manager.update_template_effectiveness("general_rewrite", 0.7)
    
    # Professional scenario should return the professional template (higher score)
    best_template = await meta_prompt_manager.get_best_template_for_scenario("professional")
    
    assert best_template.id == "professional_email_rewrite"
    assert best_template.effectiveness_score == 0.9


@pytest.mark.asyncio
async def test_get_best_template_for_unknown_scenario(meta_prompt_manager):
    """Test getting best template for unknown scenario"""
    best_template = await meta_prompt_manager.get_best_template_for_scenario("unknown_scenario")
    
    # Should return general template as fallback
    assert best_template.id == "general_rewrite"


@pytest.mark.asyncio
async def test_get_template_performance_report(meta_prompt_manager):
    """Test generating template performance report"""
    # Set some effectiveness scores
    await meta_prompt_manager.update_template_effectiveness("general_rewrite", 0.8)
    await meta_prompt_manager.update_template_effectiveness("professional_email_rewrite", 0.9)
    
    report = await meta_prompt_manager.get_template_performance_report()
    
    assert "total_templates" in report
    assert "scenario_coverage" in report
    assert "templates" in report
    
    assert report["total_templates"] > 0
    assert report["scenario_coverage"] > 0
    assert len(report["templates"]) > 0
    
    # Check template info structure
    template_info = report["templates"][0]
    assert "id" in template_info
    assert "name" in template_info
    assert "scenario_types" in template_info
    assert "effectiveness_score" in template_info
    assert "version" in template_info


@pytest.mark.asyncio
async def test_optimize_template_selection(meta_prompt_manager):
    """Test optimizing template selection based on performance data"""
    performance_data = {
        "professional": 0.85,
        "casual": 0.75,
        "complaint": 0.90
    }
    
    await meta_prompt_manager.optimize_template_selection(performance_data)
    
    # Check that effectiveness scores were updated
    professional_template = meta_prompt_manager.templates["professional_email_rewrite"]
    casual_template = meta_prompt_manager.templates["casual_email_rewrite"]
    complaint_template = meta_prompt_manager.templates["complaint_handling_rewrite"]
    
    assert professional_template.effectiveness_score == 0.85
    assert casual_template.effectiveness_score == 0.75
    assert complaint_template.effectiveness_score == 0.90


@pytest.mark.asyncio
async def test_get_template_by_id(meta_prompt_manager):
    """Test getting template by ID"""
    template = meta_prompt_manager.get_template_by_id("general_rewrite")
    
    assert template is not None
    assert template.id == "general_rewrite"
    assert isinstance(template, MetaPromptTemplate)


@pytest.mark.asyncio
async def test_get_nonexistent_template_by_id(meta_prompt_manager):
    """Test getting non-existent template by ID"""
    template = meta_prompt_manager.get_template_by_id("nonexistent_template")
    
    assert template is None


@pytest.mark.asyncio
async def test_list_available_templates(meta_prompt_manager):
    """Test listing all available templates"""
    templates = meta_prompt_manager.list_available_templates()
    
    assert isinstance(templates, list)
    assert len(templates) > 0
    assert all(isinstance(t, MetaPromptTemplate) for t in templates)


@pytest.mark.asyncio
async def test_get_scenarios_for_template(meta_prompt_manager):
    """Test getting scenarios that use a specific template"""
    scenarios = meta_prompt_manager.get_scenarios_for_template("professional_email_rewrite")
    
    assert isinstance(scenarios, list)
    assert "professional" in scenarios
    assert "business" in scenarios


@pytest.mark.asyncio
async def test_get_scenarios_for_nonexistent_template(meta_prompt_manager):
    """Test getting scenarios for non-existent template"""
    scenarios = meta_prompt_manager.get_scenarios_for_template("nonexistent_template")
    
    assert scenarios == []


@pytest.mark.asyncio
async def test_meta_prompt_template_dataclass():
    """Test MetaPromptTemplate dataclass functionality"""
    template = MetaPromptTemplate(
        id="test_template",
        name="Test Template",
        description="A test template",
        template="Test content",
        scenario_types=["test"],
        constraints={"test": True},
        version=2,
        effectiveness_score=0.75
    )
    
    assert template.id == "test_template"
    assert template.name == "Test Template"
    assert template.description == "A test template"
    assert template.template == "Test content"
    assert template.scenario_types == ["test"]
    assert template.constraints == {"test": True}
    assert template.version == 2
    assert template.effectiveness_score == 0.75


@pytest.mark.asyncio
async def test_meta_prompt_template_default_effectiveness():
    """Test MetaPromptTemplate default effectiveness score"""
    template = MetaPromptTemplate(
        id="test",
        name="Test",
        description="Test",
        template="Test",
        scenario_types=["test"],
        constraints={},
        version=1
    )
    
    assert template.effectiveness_score == 0.0  # Default value


@pytest.mark.asyncio
async def test_scenario_mapping_integrity(meta_prompt_manager):
    """Test that scenario mappings are consistent with templates"""
    for scenario, template_id in meta_prompt_manager.scenario_mappings.items():
        # Template should exist
        assert template_id in meta_prompt_manager.templates
        
        # Template should include this scenario
        template = meta_prompt_manager.templates[template_id]
        assert scenario in template.scenario_types


@pytest.mark.asyncio
async def test_template_constraint_handling():
    """Test template constraint merging with runtime constraints"""
    manager = MetaPromptManager()
    
    # Get template with built-in constraints
    professional_template = manager.templates["professional_email_rewrite"]
    assert "tone" in professional_template.constraints
    assert "max_length" in professional_template.constraints
    
    # Apply additional runtime constraints
    runtime_constraints = {"urgency": "high", "audience": "executives"}
    
    prompt = await manager.get_meta_prompt("professional", runtime_constraints)
    
    # Should include both built-in and runtime constraints
    assert "professional" in prompt  # Built-in tone constraint
    assert "immediate action" in prompt  # Runtime urgency constraint
    assert "executives" in prompt  # Runtime audience constraint


@pytest.mark.asyncio
async def test_default_template_content_quality():
    """Test that default templates contain expected quality indicators"""
    manager = MetaPromptManager()
    
    # Professional template should contain business-oriented guidance
    prof_template = manager.templates["professional_email_rewrite"]
    content = prof_template.template.lower()
    assert "professional" in content
    assert "business" in content
    assert "etiquette" in content
    
    # Casual template should contain friendly guidance
    casual_template = manager.templates["casual_email_rewrite"]
    content = casual_template.template.lower()
    assert "casual" in content
    assert "friendly" in content
    assert "conversational" in content
    
    # Complaint template should contain empathy guidance
    complaint_template = manager.templates["complaint_handling_rewrite"]
    content = complaint_template.template.lower()
    assert "empathy" in content
    assert "complaint" in content
    assert "solution" in content