def get_rephrase_response_layout(text: str, paraphrased_text: str, user_id: str):
    return {
        "response_type": "ephemeral",
        "user_id": user_id,
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
                    "text": "*Suggested Text:*\n" + paraphrased_text
                },
            },
            {
                "type": "input",
                "block_id": "tone_input_block",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "tone_input",
                    "placeholder": {
                        "type": "plain_text",
                        "text": "e.g., formal, casual, professional"
                    }
                },
                "label": {
                    "type": "plain_text",
                    "text": "Optional: Specify tone for rewrite"
                },
                "optional": True
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
                    }
                ]
            }
        ]
    }

def get_processing_layout():
    return {
        "response_type": "ephemeral",
        "text": "Hold on, we're working on it..."
    }

# def get_modify_layout(text: str, user_id: str):
#     return {
#         "response_type": "ephemeral",
#         "user_id": user_id,
#         "blocks": [
#             {
#                 "type": "section",
#                 "text": {
#                     "type": "mrkdwn",
#                     "text": "*Modify Text:*"
#                 }
#             },
#             {
#                 "type": "input",
#                 "block_id": "modify_input_block",
#                 "element": {
#                     "type": "plain_text_input",
#                     "action_id": "modified_text_input",
#                     "initial_value": text,
#                     "multiline": True
#                 },
#                 "label": {
#                     "type": "plain_text",
#                     "text": "Edit your text below:"
#                 }
#             },
#             {
#                 "type": "actions",
#                 "elements": [
#                     {
#                         "type": "button",
#                         "text": {
#                             "type": "plain_text",
#                             "text": "Cancel"
#                         },
#                         "action_id": "cancel_modify_button",
#                         "style": "danger"
#                     },
#                     {
#                         "type": "button",
#                         "text": {
#                             "type": "plain_text",
#                             "text": "Send"
#                         },
#                         "action_id": "send_modified_button",
#                         "style": "primary"
#                     }
#                 ]
#             }
#         ]
#     }

def get_error_layout(error: str, original_text: str):   
    return {
        "response_type": "ephemeral",
        "text": f"Error: {error}\n\nOriginal Text: {original_text}"
    }

def get_acknowledgment_layout(user_id: str):
    return {
        "response_type": "ephemeral",
        "user_id": user_id,
        "text": "We've received your request"
    }
