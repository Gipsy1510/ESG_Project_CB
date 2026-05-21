# ESG Question Typologies

The objective is to evaluate the ESG assistant across several types of questions. For the final project, we aim to create around 10 to 20 questions per typology. A subset of questions should include a manual answer prepared by the team, so that we can compare the assistant's answer against a human reference.

## 1. Data point extraction

These questions ask for a specific ESG data point.

Examples:
What are the company's Scope 1 and Scope 2 emissions?
What are the company's Scope 3 emissions?
What are the company's total GHG emissions in 2023?
What is the company's renewable electricity production?
What is the company's water consumption?
What is the company's total number of employees?

Expected evaluation:
The assistant should retrieve the page containing the data point and answer with the exact value, unit, year, and source page.

## 2. Disclosure existence

These questions check whether the company discloses a specific ESG item.

Examples:
Does the company disclose Scope 1 and Scope 2 emissions?
Does the company disclose Scope 3 emissions?
Does the company disclose a climate transition plan?
Does the company disclose EU Taxonomy indicators?
Does the company disclose biodiversity related risks?
Does the company disclose employee related indicators?

Expected evaluation:
The assistant should answer yes, no, or partially, and cite the page where the disclosure appears.

## 3. Numerical table interpretation

These questions require reading and interpreting tables.

Examples:
What percentage of CapEx is aligned with the EU Taxonomy?
What percentage of turnover is eligible under the EU Taxonomy?
What is the difference between eligible CapEx and aligned CapEx?
What is the total Scope 1 plus Scope 2 emissions in 2023?
What is the change in emissions compared with the baseline year?

Expected evaluation:
The assistant should identify the correct row, column, year, perimeter, unit, and source page. It should not confuse eligible with aligned, turnover with CapEx, or activity rows with the total row.

## 4. Strategy summary

These questions ask for a structured summary of a strategy or plan.

Examples:
What is the company's climate transition plan?
What are the main decarbonization levers disclosed by the company?
How does the company describe its energy transition strategy?
What are the company's main climate targets?
What are the company's main ESG priorities?

Expected evaluation:
The assistant should summarize only what is supported by the retrieved excerpts and clearly state limitations if the evidence is incomplete.

## 5. Requirement check

These questions ask whether the company appears to meet a specific ESG disclosure requirement.

Examples:
Does the company provide enough information to assess its climate transition plan?
Does the company disclose quantitative climate targets?
Does the company provide evidence on EU Taxonomy aligned CapEx?
Does the company provide information on climate governance?
Does the company disclose social or employee related indicators?

Expected evaluation:
The assistant should classify the answer as fully disclosed, partially disclosed, or not found, and explain the evidence behind the classification.

## 6. Risk and governance

These questions focus on ESG governance, risk oversight, and controls.

Examples:
How does the company govern climate related issues?
Does the board oversee climate strategy?
Does executive compensation include ESG or climate criteria?
What climate risks does the company identify?
Does the company describe biodiversity or water related risks?

Expected evaluation:
The assistant should retrieve governance or risk related evidence and cite the relevant pages.