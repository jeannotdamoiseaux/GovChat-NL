import hashlib
import hmac
import logging
import time
from string import punctuation
from typing import Any, Optional
from urllib.parse import quote

import jwt
from fastapi import Request
from open_webui.env import (
    ENABLE_FORWARD_USER_INFO_HEADERS,
    FORWARD_SESSION_INFO_HEADER_CHAT_ID,
    FORWARD_USER_INFO_HEADER_AUTH_TYPE,
    FORWARD_USER_INFO_HEADER_JWT,
    FORWARD_USER_INFO_HEADER_JWT_EXPIRES_SECONDS,
    FORWARD_USER_INFO_HEADER_JWT_SECRET,
    FORWARD_USER_INFO_HEADER_USER_EMAIL,
    FORWARD_USER_INFO_HEADER_USER_ID,
    FORWARD_USER_INFO_HEADER_USER_NAME,
    FORWARD_USER_INFO_HEADER_USER_ROLE,
    FORWARD_USER_INFO_PSEUDONYM_LENGTH,
    FORWARD_USER_INFO_PSEUDONYM_SECRET,
)
from open_webui.models.groups import Groups

log = logging.getLogger(__name__)

USER_GROUPS_PLACEHOLDERS = ('{{USER_GROUPS}}', '{{USER_GROUP_IDS}}')


def normalize_bearer_token(token: Any) -> str:
    return token.strip() if isinstance(token, str) else token or ''


def bearer_auth_header(token: Any) -> dict[str, str]:
    token = normalize_bearer_token(token)
    return {'Authorization': f'Bearer {token}'} if token else {}


def get_json_bearer_headers(token: Any = '') -> dict[str, str]:
    return {'Content-Type': 'application/json', **bearer_auth_header(token)}


def _mint_forward_user_jwt(user: Any) -> str:
    now = int(time.time())
    payload = {
        'sub': str(user.id),
        'email': str(user.email),
        'name': str(user.name),
        'role': str(user.role),
        'iss': 'open-webui',
        'iat': now,
        'exp': now + FORWARD_USER_INFO_HEADER_JWT_EXPIRES_SECONDS,
    }
    return jwt.encode(payload, FORWARD_USER_INFO_HEADER_JWT_SECRET, algorithm='HS256')


def include_user_info_headers(headers: dict, user: Optional[Any] = None, *, request=None) -> dict:
    """
    Forward user identity to external backends: signed JWT in
    FORWARD_USER_INFO_HEADER_JWT if FORWARD_USER_INFO_HEADER_JWT_SECRET is set;
    otherwise the legacy X-OpenWebUI-User-* headers.
    Include the verified incoming auth type when a request provides it.
    """
    if user is None:
        return headers

    auth_type = getattr(getattr(request, 'state', None), 'auth_type', None)
    if auth_type in ('api_key', 'jwt'):
        headers = {**headers, FORWARD_USER_INFO_HEADER_AUTH_TYPE: auth_type}

    if FORWARD_USER_INFO_HEADER_JWT_SECRET:
        try:
            token = _mint_forward_user_jwt(user)
            return {**headers, FORWARD_USER_INFO_HEADER_JWT: token}
        except Exception:
            log.exception(
                'Failed to mint %s; falling back to plain user-info headers.',
                FORWARD_USER_INFO_HEADER_JWT,
            )

    return {
        **headers,
        FORWARD_USER_INFO_HEADER_USER_NAME: quote(user.name.strip(), safe=' '),
        FORWARD_USER_INFO_HEADER_USER_ID: user.id,
        FORWARD_USER_INFO_HEADER_USER_EMAIL: user.email.strip(),
        FORWARD_USER_INFO_HEADER_USER_ROLE: user.role,
    }


def custom_headers_require_user_groups(custom_headers: Optional[dict]) -> bool:
    if not custom_headers or not isinstance(custom_headers, dict):
        return False
    return any(
        placeholder in str(value) for value in custom_headers.values() for placeholder in USER_GROUPS_PLACEHOLDERS
    )


async def get_user_groups_for_custom_headers(
    custom_headers: Optional[dict], user: Optional[Any] = None
) -> Optional[list]:
    """Fetch the user's groups only when a header value actually references a groups placeholder."""
    if user is None or not custom_headers_require_user_groups(custom_headers):
        return None

    try:
        return await Groups.get_groups_by_member_id(user.id, include_inherited=True)
    except Exception:
        log.exception('Failed to resolve user groups for custom headers')
        return None


async def get_custom_headers(custom_headers: dict, user=None, metadata: dict = None, request=None) -> dict:
    user_groups = await get_user_groups_for_custom_headers(custom_headers, user)
    return parse_custom_headers(custom_headers, user, metadata, request=request, user_groups=user_groups)


def pseudonymize(value: str) -> str:
    """
    Stable HMAC-SHA256 pseudonym for *value*, for gateways that need to attribute
    usage per user without receiving a directly identifying value.

    Returns an empty string when no salt is configured, so a missing
    FORWARD_USER_INFO_PSEUDONYM_SECRET drops the placeholder rather than silently
    forwarding the raw identifier.
    """
    if not value or not FORWARD_USER_INFO_PSEUDONYM_SECRET:
        return ''

    digest = hmac.new(
        FORWARD_USER_INFO_PSEUDONYM_SECRET.encode('utf-8'),
        value.encode('utf-8'),
        hashlib.sha256,
    ).hexdigest()
    return digest[:FORWARD_USER_INFO_PSEUDONYM_LENGTH]


def build_template_vars(
    user=None, metadata: dict = None, request=None, user_groups: list | None = None
) -> dict[str, str]:
    """Placeholder values shared by the per-connection `headers` and `body` templates."""
    metadata = metadata or {}

    # UA from the live request; fall back to metadata for detached RAG/tool calls.
    user_agent = ''
    if request is not None:
        try:
            user_agent = request.headers.get('user-agent', '') or ''
        except Exception:
            user_agent = ''
    if not user_agent:
        user_agent = metadata.get('user_agent', '') or ''

    # Extract user_message info for tree mapping
    user_message = metadata.get('user_message') or {}
    user_message_id = metadata.get('user_message_id', '') or (user_message.get('id', '') if user_message else '')
    user_message_parent_id = user_message.get('parentId', '') if user_message else ''

    user_id = (user.id if user else '') or ''
    user_email = (user.email.strip() if user else '') or ''

    return {
        '{{CHAT_ID}}': metadata.get('chat_id', '') or '',
        '{{MESSAGE_ID}}': metadata.get('message_id', '') or '',
        '{{USER_MESSAGE_ID}}': user_message_id or '',
        '{{USER_MESSAGE_PARENT_ID}}': user_message_parent_id or '',
        '{{FILE_ID}}': metadata.get('file_id', '') or '',
        '{{FILE_NAME}}': metadata.get('file_name', '') or '',
        '{{FILE_CONTENT_TYPE}}': metadata.get('file_content_type', '') or '',
        '{{TASK}}': metadata.get('task', '') or '',
        '{{MODEL_ID}}': metadata.get('model_id', '') or '',
        '{{USER_ID}}': user_id,
        '{{USER_NAME}}': (user.name.strip() if user else '') or '',
        '{{USER_EMAIL}}': user_email,
        '{{USER_ROLE}}': (user.role if user else '') or '',
        '{{USER_GROUPS}}': ','.join(group.name.strip() for group in user_groups) if user_groups else '',
        '{{USER_GROUP_IDS}}': ','.join(group.id for group in user_groups) if user_groups else '',
        '{{USER_AGENT}}': user_agent,
        '{{USER_ID_HASH}}': pseudonymize(user_id),
        '{{USER_EMAIL_HASH}}': pseudonymize(user_email),
        '{{AUTH_TYPE}}': getattr(getattr(request, 'state', None), 'auth_type', None) or '',
    }


def parse_custom_headers(
    custom_headers: dict, user=None, metadata: dict = None, request=None, user_groups: Optional[list] = None
) -> dict:
    if not custom_headers or not isinstance(custom_headers, dict):
        return {}

    template_vars = build_template_vars(user, metadata, request=request, user_groups=user_groups)

    parsed_headers = {}
    for key, value in custom_headers.items():
        if not isinstance(value, str):
            value = str(value)
        for token, val in template_vars.items():
            value = value.replace(token, val)
        # Encode Unicode and controls after substitution; preserve ASCII header syntax and existing escapes.
        parsed_headers[key] = quote(value, safe=punctuation + ' \t')

    return parsed_headers


def _substitute(value: Any, template_vars: dict[str, str]) -> Any:
    """Apply {{PLACEHOLDER}} substitution to every string nested inside *value*."""
    if isinstance(value, str):
        for token, val in template_vars.items():
            value = value.replace(token, val)
        return value
    if isinstance(value, dict):
        return {key: _substitute(item, template_vars) for key, item in value.items()}
    if isinstance(value, list):
        return [_substitute(item, template_vars) for item in value]
    return value


def _drop_empty(value: Any) -> Any:
    """
    Drop keys whose templated value resolved to nothing, so an unavailable
    placeholder (no chat_id on a task request, say) leaves the key out entirely
    instead of sending an empty string upstream.
    """
    if isinstance(value, dict):
        pruned = {key: _drop_empty(item) for key, item in value.items()}
        return {key: item for key, item in pruned.items() if item not in ('', {}, [])}
    if isinstance(value, list):
        return [_drop_empty(item) for item in value]
    return value


# Content-bearing keys a `body` template must never overwrite; a deep merge onto these
# would corrupt the conversation rather than annotate the request.
RESERVED_BODY_KEYS = frozenset({'messages', 'input', 'model', 'stream'})


def parse_custom_body(
    custom_body: dict, user=None, metadata: dict = None, request=None, user_groups: list | None = None
) -> dict:
    """
    Resolve a per-connection `body` template into the fields to merge into an
    outgoing request payload. Same placeholders as `headers`, but nested values are
    preserved, which is what gateways expecting a structured field want (for example
    Databricks `usage_context`).
    """
    if not custom_body or not isinstance(custom_body, dict):
        return {}

    reserved = RESERVED_BODY_KEYS.intersection(custom_body)
    if reserved:
        log.warning('Ignoring reserved key(s) %s in connection body template', ', '.join(sorted(reserved)))
        custom_body = {key: value for key, value in custom_body.items() if key not in RESERVED_BODY_KEYS}

    template_vars = build_template_vars(user, metadata, request=request, user_groups=user_groups)
    return _drop_empty(_substitute(custom_body, template_vars))


async def get_custom_body(custom_body: dict, user=None, metadata: dict = None, request=None) -> dict:
    user_groups = await get_user_groups_for_custom_headers(custom_body, user)
    return parse_custom_body(custom_body, user, metadata, request=request, user_groups=user_groups)


async def get_headers_and_cookies(
    request: Request,
    url,
    key=None,
    config=None,
    metadata: dict | None = None,
    user=None,
):
    config = config or {}
    cookies = getattr(request, 'cookies', {}) if config.get('forward_cookies', False) else {}
    headers = {
        'Content-Type': 'application/json',
        **(
            {
                # LICENSE covers this Open WebUI upstream metadata identifier.
                # Do not alter, remove, obscure, or replace it except as LICENSE permits:
                # https://docs.openwebui.com/license.
                'HTTP-Referer': 'https://openwebui.com/',
                'X-Title': 'Open WebUI',
            }
            if 'openrouter.ai' in url
            else {}
        ),
    }

    if ENABLE_FORWARD_USER_INFO_HEADERS and user:
        headers = include_user_info_headers(headers, user, request=request)
        if metadata and metadata.get('chat_id'):
            headers[FORWARD_SESSION_INFO_HEADER_CHAT_ID] = metadata.get('chat_id')

    token = None
    auth_type = config.get('auth_type')

    if auth_type == 'bearer' or auth_type is None:
        # Default to bearer if not specified
        token = key
    elif auth_type == 'none':
        token = None
    elif auth_type == 'session':
        token = request.state.token.credentials
    elif auth_type == 'system_oauth':
        oauth_token = None
        try:
            if request.cookies.get('oauth_session_id', None):
                oauth_token = await request.app.state.oauth_manager.get_oauth_token(
                    user.id,
                    request.cookies.get('oauth_session_id', None),
                )
        except Exception as e:
            log.error(f'Error getting OAuth token: {e}')

        if oauth_token:
            token = f'{oauth_token.get("access_token", "")}'

    elif auth_type in ('azure_ad', 'microsoft_entra_id'):
        token = get_microsoft_entra_id_access_token()

    if token:
        headers['Authorization'] = f'Bearer {token}'

    if config.get('headers') and isinstance(config.get('headers'), dict):
        custom_headers = await get_custom_headers(config.get('headers'), user, metadata, request=request)
        headers.update(custom_headers)

    return headers, cookies


def get_microsoft_entra_id_access_token():
    """
    Get Microsoft Entra ID access token using DefaultAzureCredential for Azure OpenAI.
    Returns the token string or None if authentication fails.
    """
    from azure.identity import DefaultAzureCredential, get_bearer_token_provider

    try:
        token_provider = get_bearer_token_provider(
            DefaultAzureCredential(), 'https://cognitiveservices.azure.com/.default'
        )
        return token_provider()
    except Exception as e:
        log.error(f'Error getting Microsoft Entra ID access token: {e}')
        return None
