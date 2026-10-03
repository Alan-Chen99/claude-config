# mcp__claude_ai_Indeed__get_company_data

## attributes

```json
{
  "eager_input_streaming": true,
  "defer_loading": true
}
```

## description

Primary tool for retrieving comprehensive company information from Indeed's global
knowledge base, including verified employee reviews, compensation data, and workplace
ratings. Use this tool whenever the user asks ANY question about a specific company,
including: work culture, salaries, CEO information, benefits, work-life balance,
employee satisfaction, management ratings, company size, industry, or any other
employer-related inquiry. Invoke when users want to evaluate an employer or make
informed job/career decisions.
Always display the company page url provided so they can access the company page for more information.


## input_schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "companyName": {
      "type": "string",
      "description": "The name of the company the user wants information about. Limit this to only one company, even if the user asks about multiple. If there is no company specified, do not call this tool."
    },
    "language": {
      "type": "string",
      "description": "The 2-letter ISO language code for the query results (e.g., en, es, fr, de, ja, hi). Use the language code that matches the user's preferred language or the language of the region they are querying."
    },
    "location": {
      "type": "object",
      "properties": {
        "country": {
          "type": "string",
          "description": "The 2-letter ISO country code indicating which regional Indeed site to query (e.g., US, GB, CA, DE, FR, JP, IN, AU). This represents the country where the user is looking for company information."
        },
        "usState": {
          "type": [
            "string",
            "null"
          ],
          "description": "The name of the state or province. Providing this will localize data to that state/province. Pass null for general company information and national statistics. Only provide when user specifically requests data for a particular state or province."
        },
        "usStateCode": {
          "type": [
            "string",
            "null"
          ],
          "description": "The 2-letter state/province code (e.g., CA for California). Providing this will localize data to that state/province. Pass null for general company information and national statistics. Only provide when user specifically requests data for a particular state or province."
        },
        "usCity": {
          "type": [
            "string",
            "null"
          ],
          "description": "The name of the city. Providing this will localize data to that city. Pass null for general company information and national statistics. Only provide when user specifically requests data for a particular city."
        }
      },
      "required": [
        "country",
        "usState",
        "usStateCode",
        "usCity"
      ],
      "additionalProperties": false
    },
    "jobTitle": {
      "type": "string",
      "description": "\n    The job title the user is interested in. This should be a standardized job title you might see on a resume or job post,\n    NOT a descriptor like \"entry level\" or a skill like \"communication\". Limit this to only one job title, even if the user asks about multiple.\n    If there is no job title, omit the field. Try to extract the job title from the conversation or user information provided to you.\n    Salary information can only be queried with a job title. If the user asks about salary but there is no job title, try to infer the job title from the conversation or ask for a job title before calling this tool.\n"
    },
    "knowledgeCategories": {
      "type": "object",
      "properties": {
        "metadata": {
          "type": "boolean",
          "description": "\n    Metadata about the company, including the location, contact information, CEO information, company description, number of employees, etc. This also includes content that the employer has written about themselves, including promotional content.\n     Return true if the user's question could be answered by any information in the metadata category, or false otherwise.\n     If you are not sure, return true.\n"
        },
        "ratings": {
          "type": "boolean",
          "description": "\n    User-generated ratings about the company, provided by current or former employees.\n     This includes overall rating and specific ratings for culture, job security, advancement, management, work-life balance, compensation, CEO approval, whether they recommend a friend to work at this company, and how they feel about the interview process.\n     This also includes Indeed's happiness data, which measures how employees rate things like compensation, achievement, appreciation, energy, support, purpose, learning, inclusion, flexibility, trust, belonging, and management.\n     Return true if the user's question could be answered by any information in the ratings category, or false otherwise.\n     If you are not sure, return true.\n"
        },
        "salaries": {
          "type": "boolean",
          "description": "\n    This includes the average salary for various job titles in the company.\n     You may only query for salaries with a specific job title. If the user wants to know salary information but does not provide a job title, try to infer the job title from the conversation or ask for a job title before calling this tool.\n     Return true of the user's question could be answered by any information in the salaries category, or false otherwise.\n     If you are not sure, return true.\n"
        }
      },
      "required": [
        "metadata",
        "ratings",
        "salaries"
      ],
      "additionalProperties": false
    }
  },
  "required": [
    "companyName",
    "language",
    "location",
    "knowledgeCategories"
  ],
  "additionalProperties": false
}
```
