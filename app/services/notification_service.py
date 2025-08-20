def notify_client(client_email: str, service_url: str, lead_source_type: str):
    """
    Envia uma notificação por email ao cliente.
    NOTA: Esta é uma simulação. Para produção, integre com um serviço como o SendGrid.
    """
    subject = "A sua nova instância BCL Activate está pronta!"
    
    if lead_source_type == 'webhook':
        body = f"""
        Olá,

        A sua campanha BCL Activate foi provisionada com sucesso!

        Por favor, use o seguinte Webhook URL para conectar à sua fonte de leads:
        {service_url}/activate

        Cumprimentos,
        Equipa Blue Digital Solutions
        """
    else: # Assumimos 'meta' ou outros
        body = f"""
        Olá,

        A sua campanha BCL Activate está ativa! O nosso sistema já se conectou à sua conta.
        Os novos leads serão processados automaticamente.

        URL do Serviço: {service_url}

        Cumprimentos,
        Equipa Blue Digital Solutions
        """

    print("\n--- SIMULAÇÃO DE ENVIO DE EMAIL ---")
    print(f"PARA: {client_email}")
    print(f"ASSUNTO: {subject}")
    print(f"CORPO:\n{body}")
    print("-----------------------------------\n")
    
    return True