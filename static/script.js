document.getElementById('generate-contract').addEventListener('click', function () {
    const form = document.getElementById('cadastro-form');
    const nome = form.querySelector('input[name="nome"]').value.trim();
    const telefone = form.querySelector('input[name="telefone"]').value.trim();
    const email = form.querySelector('input[name="email"]').value.trim();
    const cidadeOrigem = form.querySelector('input[name="cidade_origem"]').value.trim();
    const cidadeObra = form.querySelector('input[name="cidade_obra"]').value.trim();
    const quantidadeTijolos = form.querySelector('input[name="quantidade_tijolos"]').value.trim();
    const valor = form.querySelector('input[name="valor"]').value.trim();

    // Verificar campos obrigatórios
    if (!nome || !telefone || !email || !cidadeOrigem || !cidadeObra || !quantidadeTijolos || !valor) {
        alert('Por favor, preencha todos os campos obrigatórios antes de gerar o contrato.');
        return;
    }

    // Enviar os dados para a rota de geração de contrato
    form.action = '/gerar-contrato';
    form.method = 'POST';
    form.submit();
});

document.getElementById('cpf-cnpj').addEventListener('input', function (e) {
    let value = e.target.value.replace(/\D/g, ''); // Remove tudo que não for número

    if (value.length <= 11) {
        // Formatar como CPF: 000.000.000-00
        value = value.replace(/(\d{3})(\d)/, '$1.$2');
        value = value.replace(/(\d{3})(\d)/, '$1.$2');
        value = value.replace(/(\d{3})(\d{1,2})$/, '$1-$2');
    } else {
        // Formatar como CNPJ: 00.000.000/0000-00
        value = value.replace(/^(\d{2})(\d)/, '$1.$2');
        value = value.replace(/^(\d{2})\.(\d{3})(\d)/, '$1.$2.$3');
        value = value.replace(/\.(\d{3})(\d)/, '.$1/$2');
        value = value.replace(/(\d{4})(\d)/, '$1-$2');
    }

    e.target.value = value;
});