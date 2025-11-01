# First meeting script

## Questions:

Who are the product users, stakeholders?

What problems do you have with calendars? Have you some user stories scenario which we need to resolve these problems in tg bot? 

Why are you need Telegram Bot? Interface should be only telegram bot interface or we also need web app?

What main features you want to see? (clarifying questions below)

Do we need feature that bot showing all events? or only notification sending?

Do we need add/delete/edit events via bot interface? 

You need the bot for personal usage or for groups? The bot should write in private messages to the user or in group chats, to which the chat owner will add it?

Do need to set the frequency of notifications (including how long before the event the notifications should arrive)?

What calendars are you using and what calendar events do you need in TG bot? There is two ways to do integration of calendars:

- using ical link to calendar (the user will have to login to the calendar he uses, copy the ics link from there and paste it to bot)

- The user will be able to login to their calendar account via a bot (for example, via a web app), but if we want this functionality - we need to determ ine which calendars the bot will integrate with

Do we need voice input, AI integration? if yes - justify why we need voice/AI. 

Which languages bot interface must to support?

Do we need setting where user specify time zone or we need determine time zone via user current location?

Do we need to user able mute bot for a while? on example at night time or weekends.

Do we need to sending daily plans (events list on today)?

Do we need to export events from bot?

What additional requirements you have?

## Mom test

The questions were originally compiled based on the considerations described in the notes. We also knew mom test before that (we learnt it at the requirements engineering course). The questions were originally formulated in such a way that they could be answered unambiguously and unbiasedly. 

On example: `what do you want to see in TG bot?` -> `What problems do you have with calendars?` and `how to integrate calendar events into TG bot` -> `what calendars are you using and what calendar events do you need in TG bot?`


## Notes

1. The problem was explained and understood before the interview, so there was no point in asking what problem we were solving.
    ```
    Otherwise, the questions would be aimed primarily at clarifying the problem, focusing on the person's real experiences and behaviors.
    ```
2. A market analysis was conducted before the interview, therefore, we had an idea of which features could be implemented, an approximate vision of the project was formed, it only remained to clarify with the customer the choice between different feature options.
    ```
    There is no need to come up with innovative solution to the problem, the solutions available on the market to one degree or another cover the functionality necessary for an optimal solution to the problem. Our goal is to determine which functionality of our project will satisfy the customer's expectations and solve his problem, for which many ideas can be borrowed from existing solutions.
    ```
    
3.  The customer is a technically skilled person, which made it possible to communicate with him in his language, which accelerated the process.
    ```
    Otherwise, the questions would not contain about technical aspects, would be reformulated in such a way that they would be understood by anyone, would be more aimed at user experience, as well as would help the customer determine his expectations, perhaps would direct him to the necessary reflections on the problem.
    ```