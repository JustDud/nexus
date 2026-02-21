# frozen_string_literal: true

module AcmePortal
  class AccountSerializer
    def initialize(account)
      @account = account
    end

    def as_json(*)
      {
        id: @account.id,
        name: @account.name,
        status: @account.status,
        active: @account.active?
      }
    end
  end
end
