# 12. Załączniki

Lista dostępnych diagramów i załączników (lokalizacja i pliki):

- Szczegółowe diagramy w `Inzynierka/Inżynierka_01/12_ZALACZNIKI/diagramy/`:
  - [architektura_systemu.mmd](Inzynierka/Inżynierka_01/12_ZALACZNIKI/diagramy/architektura_systemu.mmd)
  - [erd_smarthome.mmd](Inzynierka/Inżynierka_01/12_ZALACZNIKI/diagramy/erd_smarthome.mmd)
  - [sekwencje_toggle_device.mmd](Inzynierka/Inżynierka_01/12_ZALACZNIKI/diagramy/sekwencje_toggle_device.mmd)
  - [sekwencje_automation.mmd](Inzynierka/Inżynierka_01/12_ZALACZNIKI/diagramy/sekwencje_automation.mmd)
  - [sekwencje_login.mmd](Inzynierka/Inżynierka_01/12_ZALACZNIKI/diagramy/sekwencje_login.mmd)
  - [deployment_docker.mmd](Inzynierka/Inżynierka_01/12_ZALACZNIKI/diagramy/deployment_docker.mmd)

- Pliki Mermaid utworzone w `Inzynierka/Inżynierka_02/diagrams/` (lokalne diagramy wykorzystane w pracy):
  - database_layer.mmd
  - client_connection.mmd
  - websocket_control_flow.mmd
  - automation_execution.mmd
  - automation_trigger.mmd
  - device_model.mmd
  - invitation_flow.mmd

Jak generować obrazy z Mermaid lokalnie (opcja):

```powershell
npm install -g @mermaid-js/mermaid-cli
mmdc -i diagrams/database_layer.mmd -o diagrams/database_layer.svg
```
