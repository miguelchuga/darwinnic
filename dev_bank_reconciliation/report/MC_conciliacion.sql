CREATE OR REPLACE VIEW public."MC_conciliacion"
AS SELECT br.id AS id_conciliacion,
    br.journal_op_id,
    br.start_balance,
    br.journal_id AS id_diario_conciliacion,
    br.state,
    br.start_date,
    br.end_date,
    br.name AS descripcion_conciliacion,
    br.account_rec_id,
    br.end_balance,
    aml.ref,
    aml.name AS nombre_linea,
    aml.id AS id_apunte,
    aml.journal_id AS id_diario_apunte,
    aml.date,
    aml.date_maturity,
    aml.partner_id,
    case 
    	when rc."name" = 'USD' and aml.credit = 0 then aml.amount_currency
    	else aml.debit
	end debit,
	case 
		when rc."name" = 'USD' and aml.debit = 0 then abs(aml.amount_currency)
		else aml.credit
	end credit,
    aml.balance,
    aml.amount_currency,
    aml.is_not_confirm,
    aml.is_bank_reconcile,
    ap.communication AS concepto,
    ap.x_cheque_manual,
    ap.x_deposito,
    ap.check_number,
    ap.payment_type,
    rp.name AS nombre_partner,
    case 
    	when ap.check_number is not null then cast(ap.check_number as text)
    	when ap.x_transaccion is not null then cast(ap.x_transaccion as text)
    	else am."ref"
	end document_number,
    am."name" as move_name
   FROM bank_reconciliation br
     JOIN account_move_line aml ON aml.account_id = br.account_rec_id
     JOIN account_move_line_rel amlr ON amlr.journal_ids = br.id AND amlr.move_ids = aml.id
     LEFT JOIN account_payment ap ON ap.id = aml.payment_id
     LEFT JOIN res_partner rp ON rp.id = aml.partner_id
     left join res_currency rc on aml.currency_id = rc.id
     left join account_move am on aml.move_id = am.id;