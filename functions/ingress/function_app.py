import azure.functions as func

from cas_reference_product.ingress import InvalidIngressRequest, create_worker_message

app = func.FunctionApp(http_auth_level=func.AuthLevel.FUNCTION)


@app.route(route="workflows", methods=["POST"])
@app.queue_output(
    arg_name="worker_message",
    queue_name="%WORK_QUEUE_NAME%",
    connection="WORK_QUEUE_STORAGE",
)
def submit_workflow(
    request: func.HttpRequest,
    worker_message: func.Out[str],
) -> func.HttpResponse:
    try:
        message = create_worker_message(request.get_body())
    except InvalidIngressRequest:
        return func.HttpResponse("Invalid request.", status_code=400)

    worker_message.set(message)
    return func.HttpResponse(status_code=202)
