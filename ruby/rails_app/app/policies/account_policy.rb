# frozen_string_literal: true

module AcmePortal
  class AccountPolicy
    def initialize(user, account)
      @user = user
      @account = account
    end

    def show?
      !@user.nil? && !@account.nil?
    end

    def update?
      false
    end
  end
end
