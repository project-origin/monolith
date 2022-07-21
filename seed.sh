set -e

pipenv run python -m origin users create --subject subject1 --name "Subject 1" --company "Subject 1 Company" --email "subject1@foo.bar" --password 1234 --active
pipenv run python -m origin users create --subject subject2 --name "Subject 2" --company "Subject 2 Company" --email "subject2@foo.bar" --password 1234 --active

pipenv run python -m origin meteringpoints create --subject subject1 --gsrn 1 --type production --sector DK1 --tech T010101 --fuel F01010101
pipenv run python -m origin meteringpoints create --subject subject1 --gsrn 2 --type production --sector DK1 --tech T020202 --fuel F02020202
pipenv run python -m origin meteringpoints create --subject subject1 --gsrn 3 --type consumption --sector DK1 --tech "" --fuel ""

#pipenv run python -m origin measurements generate --gsrn 1 --from "2022-01-01 00:00" --to "2023-01-01 00:00" --min 1 --max 100
#pipenv run python -m origin measurements generate --gsrn 3 --from "2022-01-01 00:00" --to "2023-01-01 00:00" --min 1 --max 100
#pipenv run python -m origin measurements generate --gsrn 2 --from "2022-01-01 00:00" --to "2023-01-01 00:00" --min 1 --max 100

pipenv run python -m origin measurements generate --gsrn 3 --from "2022-01-01 00:00" --to "2023-01-01 00:00" --min 10 --max 10
pipenv run python -m origin measurements generate --gsrn 1 --from "2022-01-01 00:00" --to "2023-01-01 00:00" --min 100 --max 100
pipenv run python -m origin measurements generate --gsrn 2 --from "2022-01-01 00:00" --to "2023-01-01 00:00" --min 100 --max 100

pipenv run python -m origin technologies import --path ../var/technologies.csv
