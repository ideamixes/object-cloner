{{/*
The image to use
*/}}
{{- define "object-cloner.image" -}}
{{- printf "%s:%s" .Values.image.repository (default (printf "%s" .Chart.AppVersion) .Values.image.tag) }}
{{- end }}