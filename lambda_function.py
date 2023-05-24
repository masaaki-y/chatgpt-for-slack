import os
import openai
import json
import re
from slack_sdk import WebClient

def lambda_handler(event, context):
    try:
      openai.api_key = os.getenv("OPENAI_API_KEY")
      slack_client = WebClient(token=os.environ['SLACK_BOT_TOKEN'])
      slack_channel_id = os.environ['CHANNEL_ID']
      event_payload = json.loads(event['body'])

      if "thread_ts" in event_payload['event']:
        user_input_ts = event_payload['event']['thread_ts']
      else:
        user_input_ts = event_payload['event']['ts']

      chat_history = slack_client.conversations_replies(
        channel=slack_channel_id,
        ts=user_input_ts,
      )

      slack_response = slack_client.chat_postMessage(
        channel=slack_channel_id,
        text="...考え中...",
        thread_ts=user_input_ts
        )
      tmp_ts = slack_response['ts']

      user_input = event_payload['event']['text'].replace("\n", " ")
      user_input = user_input.replace("`", " ")
      user_input = re.sub("<@.*>", "", user_input)


      if len(chat_history['messages']) == 1:
        completion = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=[
            {"role": "system", "content": "あなたはとても優秀なフルスタックエンジニアです。ユーザーからの質問に対して、可能な限り最適な回答をしてください。"},
            {"role": "user", "content": user_input}
          ],
          temperature=0.1,
        )
      else:
        messages=[{"role": "system", "content": "あなたはとても優秀なフルスタックエンジニアです。ユーザーからの質問に対して、可能な限り最適な回答をしてください。"}]
 
        for h in chat_history["messages"]:
          if "client_msg_id" in h:
            messages.append({"role": "user", "content": re.sub("<@.*>", "", h['text']).replace("\n", " ")})
          elif "bot_id" in h:
            messages.append({"role": "assistant", "content": h['text']})

        completion = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=messages,
          max_tokens=2500,
          temperature=0.1,
        )

      slack_client.chat_delete(
        channel=slack_channel_id,
        ts=tmp_ts
      )
      answer_response = slack_client.chat_postMessage(
        channel=slack_channel_id,
        text=completion.choices[0].message["content"],
        thread_ts=user_input_ts
        )
    except Exception as e:
      print(event['body'])
      print(e)
      error_response = slack_client.chat_postMessage(
        channel=slack_channel_id,
        text="何らかのエラーが発生しました。質問をやりなおしてください。",
        thread_ts=user_input_ts
      )
      print(error_response)
    
    finally:
      return {
          'statusCode': 200,
          'body': json.dumps(event['body'])
      }
