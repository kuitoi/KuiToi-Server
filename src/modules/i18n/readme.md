### Builtins

```python
class i18n:
    # Basic phases
    hello: str
    config_path: str
    init_ok: str
    start: str
    stop: str

    # Server auth
    auth_need_key: str
    auth_empty_key: str
    auth_cannot_open_browser: str
    auth_use_link: str

    # GUI phases
    GUI_yes: str
    GUI_no: str
    GUI_ok: str
    GUI_cancel: str
    GUI_need_key_message: str
    GUI_enter_key_message: str
    GUI_cannot_open_browser: str

    # Web phases
    web_start: str

    # Core phrases

    core_bind_failed: str
    core_direct_mode: str
    core_auth_server_error: str
    core_auth_server_refused: str
    core_auth_server_refused_no_reason: str
    core_auth_server_refused_direct_node: str
    core_auth_server_no_response: str
    core_mods_loaded: str
    core_identifying_connection: str
    core_player_kick_outdated: str
    core_player_kick_bad_key: str
    core_player_kick_invalid_key: str
    core_player_kick_auth_server_fail: str
    core_player_kick_stale: str
    core_player_kick_no_allowed_default_reason: str
    core_player_kick_server_full: str
    core_player_set_id: str
    core_identifying_okay: str

    # In-game phrases

    game_welcome_message: str

    # Client class phrases

    client_mod_request: str
    client_mod_sent: str
    client_mod_sent_limit: str
    client_mod_sent_error: str
    client_sync_time: str
    client_kicked: str
    client_event_invalid_data: str
    client_player_disconnected: str

    # Events system

    events_not_callable: str
    events_not_found: str
    events_calling_error: str
    events_lua_function_not_found: str
    events_lua_local: str
    events_lua_calling_error: str

    # Plugins loader

    plugins_not_found_load: str
    plugins_not_found_start: str
    plugins_not_found_unload: str
    plugins_kt_invalid: str
    plugins_invalid: str
    plugins_error_loading: str

    # Lua plugins loader

    plugins_lua_enabled: str
    plugins_lua_nuances_warning: str
    plugins_lua_legacy_config_create_warning: str
    plugins_lua_legacy_config_create: str
    plugins_lua_unload: str

    # Command: man
    man_message_man: str
    help_message_man: str
    man_for: str
    man_message_not_found: str
    man_command_not_found: str

    # Command: help
    man_message_help: str
    help_message_help: str
    help_command: str
    help_message: str
    help_message_not_found: str

    # Command: stop
    man_message_stop: str
    help_message_stop: str

    # Command: exit
    man_message_exit: str
    help_message_exit: str

```