# obtener_datos.py — Módulo de obtención de datos financieros (versión simplificada)
# Todos los ratios se calculan manualmente con el precio actual en tiempo real.

import yfinance as yf


def _obtener_valor_ttm(df_quarterly, keys_posibles):
    """Suma los últimos 4 trimestres (TTM)."""
    if df_quarterly is None or df_quarterly.empty:
        return 0.0
    for k in keys_posibles:
        if k in df_quarterly.index:
            try:
                return df_quarterly.loc[k].iloc[:4].sum()
            except Exception:
                return 0.0
    return 0.0


def _obtener_dato_balance(df_balance, keys_posibles, fallback=0):
    """Coge el dato más reciente del balance."""
    if df_balance is None or df_balance.empty:
        return fallback
    for k in keys_posibles:
        if k in df_balance.index:
            try:
                return df_balance.loc[k].iloc[0]
            except Exception:
                continue
    return fallback


def obtener_datos(ticker_symbol, is_reit=False):
    """Descarga datos de Yahoo Finance y calcula ratios clave."""
    try:
        empresa = yf.Ticker(ticker_symbol)
        info = empresa.info
        fast_info = empresa.fast_info
        data = {}

        # Precio
        precio = fast_info.get('last_price') or info.get('currentPrice') or info.get('previousClose', 0)
        data['precio'] = precio

        # Market Cap (ajustado al precio actual)
        m_cap_base = fast_info.get('market_cap') or info.get('marketCap', 0)
        precio_ref = info.get('previousClose') or info.get('regularMarketPreviousClose')
        if m_cap_base and precio and precio_ref and precio_ref > 0:
            data['market_cap'] = m_cap_base * (precio / precio_ref)
        else:
            data['market_cap'] = m_cap_base or 0

        data['nombre'] = info.get('shortName', info.get('longName', ticker_symbol))
        data['is_reit'] = is_reit

        # Histórico 5 años
        data['history'] = empresa.history(period="5y")

        # DataFrames trimestrales
        q_fin = empresa.quarterly_financials
        q_cf = empresa.quarterly_cashflow
        q_bal = empresa.quarterly_balance_sheet

        # --- PER LTM = Market Cap / Net Income TTM ---
        net_income = _obtener_valor_ttm(q_fin, ['Net Income', 'Net Income Common Stockholders'])
        data['net_income_ttm'] = net_income
        if net_income > 0 and data['market_cap'] > 0:
            data['per_ltm'] = data['market_cap'] / net_income
        elif net_income < 0:
            data['per_ltm'] = -1.0
        else:
            data['per_ltm'] = 0.0

        # --- PER NTM = Precio / Forward EPS (no aplica a REITs) ---
        if is_reit:
            data['per_ntm'] = 0
        else:
            fwd_eps = info.get('forwardEps', 0)
            if fwd_eps and fwd_eps > 0 and precio:
                data['per_ntm'] = precio / fwd_eps
            else:
                data['per_ntm'] = info.get('forwardPE', 0) or 0

        # --- FCF y P/FCF ---
        capex = abs(_obtener_valor_ttm(q_cf, ['Capital Expenditure', 'Purchase Of PPE']))
        ocf = _obtener_valor_ttm(q_cf, ['Operating Cash Flow', 'Total Cash From Operating Activities'])
        fcf = ocf - capex
        data['fcf_ttm'] = fcf

        if fcf > 0 and data['market_cap'] > 0:
            data['p_fcf'] = data['market_cap'] / fcf
        elif fcf < 0:
            data['p_fcf'] = -1.0
        else:
            data['p_fcf'] = 0.0

        # --- Deuda ---
        total_debt = _obtener_dato_balance(q_bal, ['Total Debt', 'Total Debt And Capital Lease Obligation'],
                                           fallback=info.get('totalDebt', 0) or 0)
        total_cash = _obtener_dato_balance(q_bal, ['Cash And Cash Equivalents',
                                                    'Cash Cash Equivalents And Short Term Investments'],
                                           fallback=info.get('totalCash', 0) or 0)
        data['total_debt'] = total_debt
        data['total_cash'] = total_cash
        data['deuda_neta'] = total_debt - total_cash

        ebitda = _obtener_valor_ttm(q_fin, ['Normalized EBITDA', 'EBITDA'])
        if ebitda == 0:
            ebitda = info.get('ebitda', 0) or 0
        data['ebitda_ttm'] = ebitda

        # Ratio Deuda Neta / EBITDA
        if ebitda > 0:
            data['deuda_ebitda'] = (total_debt - total_cash) / ebitda
        else:
            data['deuda_ebitda'] = None

        # --- Yields ---
        raw_div = info.get('dividendYield', 0) or 0
        data['div_yield'] = raw_div / 100 if raw_div > 0.2 else raw_div

        recompras = abs(_obtener_valor_ttm(q_cf, ['Repurchase Of Capital Stock', 'Purchase Of Stock']))
        emisiones = _obtener_valor_ttm(q_cf, ['Issuance Of Capital Stock'])
        recompras_netas = recompras - emisiones
        data['buyback_yield'] = recompras_netas / data['market_cap'] if data['market_cap'] > 0 else 0.0
        data['total_yield'] = data['div_yield'] + data['buyback_yield']

        # --- REIT: P/FFO ---
        if is_reit:
            da = _obtener_valor_ttm(q_cf, ['Depreciation And Amortization',
                                            'Depreciation Amortization Depletion',
                                            'Depreciation'])
            if da == 0:
                da = _obtener_valor_ttm(q_fin, ['Depreciation And Amortization',
                                                  'Reconciled Depreciation'])
            ffo = net_income + da
            data['ffo_ttm'] = ffo
            data['p_ffo'] = data['market_cap'] / ffo if ffo > 0 and data['market_cap'] > 0 else 0.0
        else:
            data['ffo_ttm'] = 0
            data['p_ffo'] = 0

        return data

    except Exception as e:
        print(f"Error obteniendo datos para {ticker_symbol}: {e}")
        return None
