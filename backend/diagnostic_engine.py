"""
Diagnostic Engine - AI-powered client assessment
"""
from flag_config import FLAG_MATRIX
from mortality_screen import calculate_mortality_risk
from tier_validator import is_tier_mismatch
from missing_info_warning import check_missing_info
import logging

logger = logging.getLogger(__name__)


def diagnose_client_responses(text_input):
    """
    Analyze client text responses for diagnostic flags
    
    Args:
        text_input: Client's text responses
        
    Returns:
        Dictionary of flagged categories and their matched flags
    """
    profile = {k: [] for k in FLAG_MATRIX}
    lowered = text_input.lower()
    for category, flags in FLAG_MATRIX.items():
        for flag in flags:
            words = flag.lower().split()
            if any(word in lowered for word in words):
                profile[category].append(flag)
    return profile


def run_full_diagnostic(data):
    """
    Run complete diagnostic assessment on client data
    
    Args:
        data: Dictionary containing:
            - text: Client's text responses
            - age: Client's age (optional)
            - chronic: List of chronic conditions (optional)
            - habits: List of habits (optional)
            - tier: Selected tier (optional)
            - client_data: Additional client information (optional)
    
    Returns:
        Dictionary containing:
            - profile: Diagnostic flags by category
            - mortality_risk: Risk level (low/moderate/elevated/critical)
            - tier_mismatch: Whether selected tier matches risk
            - missing_info: List of missing required information
            - crisis_level: Overall crisis level (LOW/ELEVATED/CRITICAL)
            - recommended_actions: List of recommended actions
    """
    try:
        text_input = data.get('text', '')
        age = data.get('age', 0)
        chronic = data.get('chronic', [])
        habits = data.get('habits', [])
        tier = data.get('tier', '')
        client_data = data.get('client_data', {})
        
        # Run diagnostic components
        profile = diagnose_client_responses(text_input)
        mortality_risk = calculate_mortality_risk(age, chronic, habits)
        tier_mismatch = is_tier_mismatch(mortality_risk, tier) if tier else None
        missing_info = check_missing_info(client_data)
        
        # Determine overall crisis level
        crisis_level = determine_crisis_level(profile, mortality_risk)
        
        # Generate recommended actions
        recommended_actions = generate_recommendations(profile, mortality_risk, crisis_level)
        
        return {
            'profile': profile,
            'mortality_risk': mortality_risk,
            'tier_mismatch': tier_mismatch,
            'missing_info': missing_info,
            'crisis_level': crisis_level,
            'recommended_actions': recommended_actions,
            'flags_count': sum(len(flags) for flags in profile.values())
        }
        
    except Exception as e:
        logger.error(f"Diagnostic engine error: {e}")
        return {
            'error': str(e),
            'profile': {},
            'mortality_risk': 'unknown',
            'crisis_level': 'UNKNOWN'
        }


def determine_crisis_level(profile, mortality_risk):
    """
    Determine overall crisis level based on diagnostic profile and mortality risk
    
    Args:
        profile: Diagnostic flags by category
        mortality_risk: Calculated mortality risk level
        
    Returns:
        Crisis level: 'LOW', 'ELEVATED', or 'CRITICAL'
    """
    # Check for critical indicators
    critical_categories = ['suicidal_ideation', 'self_harm', 'substance_abuse']
    has_critical = any(len(profile.get(cat, [])) > 0 for cat in critical_categories)
    
    if has_critical or mortality_risk == 'critical':
        return 'CRITICAL'
    
    # Check for elevated risk indicators
    elevated_categories = ['depression', 'anxiety', 'trauma', 'financial_stress']
    elevated_count = sum(len(profile.get(cat, [])) for cat in elevated_categories)
    
    if elevated_count >= 3 or mortality_risk in ['elevated', 'high']:
        return 'ELEVATED'
    
    return 'LOW'


def generate_recommendations(profile, mortality_risk, crisis_level):
    """
    Generate recommended actions based on assessment
    
    Args:
        profile: Diagnostic flags by category
        mortality_risk: Calculated mortality risk level
        crisis_level: Overall crisis level
        
    Returns:
        List of recommended action strings
    """
    recommendations = []
    
    if crisis_level == 'CRITICAL':
        recommendations.append('Immediate crisis intervention required')
        recommendations.append('Contact emergency services if client is in immediate danger')
        recommendations.append('Schedule emergency coaching session within 24 hours')
        recommendations.append('Activate crisis response protocol')
    
    elif crisis_level == 'ELEVATED':
        recommendations.append('Schedule coaching session within 48-72 hours')
        recommendations.append('Provide additional support resources')
        recommendations.append('Monitor client closely for escalation')
    
    else:
        recommendations.append('Standard coaching session recommended')
        recommendations.append('Focus on goal-setting and action planning')
    
    # Add specific recommendations based on profile
    if len(profile.get('financial_stress', [])) > 0:
        recommendations.append('Consider financial coaching or resources')
    
    if len(profile.get('relationship_issues', [])) > 0:
        recommendations.append('Explore relationship dynamics in coaching')
    
    if len(profile.get('health_concerns', [])) > 0:
        recommendations.append('Recommend medical consultation if not already engaged')
    
    if mortality_risk in ['elevated', 'critical', 'high']:
        recommendations.append('Address health and lifestyle factors as priority')
    
    return recommendations

