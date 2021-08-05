Select * from account_move
Select * from res_users

       SELECT company_id, id,name, date_invoice, date,state
              FROM "MC_libro_compras"
             WHERE   name  <> '/' 
             
Select quantity,price_unit,* from account_move_line where id in (25,26)

Select * from account_move_line where move_id  = 10
Select * from account_account_tag_account_move_line_rel



-- Libro de compras
drop view public."MC_libro_compras";
CREATE OR REPLACE VIEW public."MC_libro_compras" AS 
 SELECT ai.company_id,
    ai.id,
    ai.name,
    ai.invoice_date AS date_invoice,
    ai.date,
    ai.state
   FROM account_move ai
     JOIN account_journal aj ON aj.id = ai.journal_id AND aj.type::text = 'purchase'::text AND ai.type = 'in_invoice' AND aj.imprime_libro::text = 'Si'::text and ai.id = 10;
 