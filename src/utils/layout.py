def get_layout(text: str, paraphrased_text: str):
    return {
        "response_type": "ephemeral",
        "user_id": "U08LH7LLYNT",
        "blocks": [
            {   
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": text
                    },
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": paraphrased_text
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
                            "text": "Modify"
                        },
                        "action_id": "modify_button"
                    },
                    {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Send"
                        },
                        "action_id": "send_button",
                        "style": "primary"
                    }
                ]
            }
        ]
    }