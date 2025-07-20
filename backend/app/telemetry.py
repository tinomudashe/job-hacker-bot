import logging
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.semconv.resource import ResourceAttributes

# Configure logging
logger = logging.getLogger(__name__)

def setup_telemetry():
    """
    Configures and initializes the OpenTelemetry SDK for the application.
    """
    try:
        # 1. Create a Resource to identify our application
        # This adds metadata to all traces, like the service name.
        resource = Resource(attributes={
            ResourceAttributes.SERVICE_NAME: "job-hacker-bot-backend",
            ResourceAttributes.SERVICE_VERSION: "1.0.0",
        })

        # 2. Set up the Tracer Provider
        # This is the core of the SDK that manages tracers.
        tracer_provider = TracerProvider(resource=resource)

        # 3. Configure the Console Exporter
        # This exporter will print all traces to the console, which is great
        # for local development and debugging.
        console_exporter = ConsoleSpanExporter()

        # 4. Create a Span Processor
        # The processor receives spans from the tracer and sends them to the
        # configured exporter(s) in batches.
        span_processor = BatchSpanProcessor(console_exporter)

        # 5. Add the processor to the provider
        tracer_provider.add_span_processor(span_processor)

        # 6. Set the global Tracer Provider
        # This makes the configured provider available across the entire application.
        trace.set_tracer_provider(tracer_provider)
        
        logger.info("✅ OpenTelemetry configured successfully with Console Exporter.")

    except Exception as e:
        logger.error(f"❌ Failed to configure OpenTelemetry: {e}", exc_info=True) 