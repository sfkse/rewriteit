def get_rephrase_result_layout(text: str, paraphrased_text: str, user_id: str):
    return {
        "response_type": "ephemeral",
        "blocks": [
            {   
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Original Text:*\n" + text
                },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Improved Text:*\n" + paraphrased_text
                },
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Rewrite"
                        },
                        "action_id": "rewrite_button"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Copy"
                        },
                        "action_id": "copy_button"
                    }
                ]
            }
        ]
    }

def get_success_layout(text: str, paraphrased_text: str, user_id: str):
    return {
        "response_type": "ephemeral",
        "text": "Text paraphrased successfully!"
    }

def get_modify_layout(text: str, user_id: str):
    return {
        "response_type": "ephemeral",
        "user_id": user_id,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": "*Modify Text:*"
                }
            },
            {
                "type": "input",
                "block_id": "modify_input_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "modified_text_input",
                    "initial_value": text,
                    "multiline": True
                },
                "label": {
                    "type": "plain_text",
                    "text": "Edit your text below:"
                }
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Cancel"
                        },
                        "action_id": "cancel_modify_button",
                        "style": "danger"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Send"
                        },
                        "action_id": "send_modified_button",
                        "style": "primary"
                    }
                ]
            }
        ]
    }

def get_error_layout(error: str):   
    return {
        "response_type": "ephemeral",
        "text": f"Error: {error}"
    }