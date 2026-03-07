from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

provider = TracerProvider()
trace.set_tracer_provider(provider)

# console debug
provider.add_span_processor(
    BatchSpanProcessor(ConsoleSpanExporter())
)

# OTLP exporter
otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4317",
    insecure=True
)

provider.add_span_processor(
    BatchSpanProcessor(otlp_exporter)
)

tracer = trace.get_tracer("agent-platform")